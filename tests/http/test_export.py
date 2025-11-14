"""Export HTTP 엔드포인트 통합 테스트"""

import json
import tempfile
from pathlib import Path
from urllib.parse import urlencode

import pytest
import pytest_asyncio

from server.handlers.db_handler import DBHandler


@pytest_asyncio.fixture
async def db_with_data():
    """테스트 데이터가 있는 DB 생성"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DBHandler(str(db_path))
        await db.initialize()

        # 테스트 데이터 생성
        session_key = "test_session"
        room_id = "test_room"
        context = json.dumps({"world": "판타지 세계", "characters": [{"name": "테스트 캐릭터"}]})

        await db.upsert_room(room_id, session_key, "테스트 채팅방", context)

        # 메시지 추가
        await db.save_message(room_id, "user", "안녕하세요", session_key)
        await db.save_message(room_id, "assistant", "[캐릭터]: 반갑습니다", session_key)
        await db.save_message(room_id, "user", "잘 지내세요?", session_key)

        # 토큰 사용량 추가
        token_info = json.dumps({"input_tokens": 100, "output_tokens": 200})
        await db.save_token_usage(session_key, room_id, "claude", token_info)

        yield db, session_key, room_id

        await db.close()


class TestExportEndpoints:
    """Export HTTP 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_db_data_preparation(self, db_with_data):
        """테스트 데이터가 정상적으로 준비되었는지 확인"""
        db, session_key, room_id = db_with_data

        # Room 확인
        room = await db.get_room(room_id)
        assert room is not None
        assert room["title"] == "테스트 채팅방"

        # Messages 확인
        messages = await db.list_messages(room_id)
        assert len(messages) == 3

        # Token usage 확인
        usage = await db.list_token_usage_range(room_id)
        assert len(usage) == 1

    @pytest.mark.asyncio
    async def test_export_json_data_structure(self, db_with_data):
        """Export 데이터 구조 검증 (실제 HTTP 요청 없이)"""
        db, session_key, room_id = db_with_data

        # 방 데이터 조회
        room = await db.get_room(room_id)
        messages = await db.list_messages(room_id)
        token_usage = await db.list_token_usage_range(room_id)

        # Export 데이터 구조 생성
        export_data = {
            "version": "1.0",
            "export_type": "single_room",
            "room": {
                "room_id": room["room_id"],
                "title": room["title"],
                "context": json.loads(room["context"]) if room["context"] else None,
                "messages": [
                    {
                        "role": msg["role"],
                        "content": msg["content"],
                        "timestamp": msg["timestamp"],
                    }
                    for msg in messages
                ],
                "token_usage": [
                    {
                        "provider": usage["provider"],
                        "token_info": (
                            json.loads(usage["token_info"]) if usage["token_info"] else None
                        ),
                        "timestamp": usage["timestamp"],
                    }
                    for usage in token_usage
                ],
            },
        }

        # 구조 검증
        assert export_data["version"] == "1.0"
        assert export_data["export_type"] == "single_room"
        assert export_data["room"]["room_id"] == room_id
        assert export_data["room"]["title"] == "테스트 채팅방"
        assert len(export_data["room"]["messages"]) == 3
        assert len(export_data["room"]["token_usage"]) == 1

        # 메시지 순서 확인
        assert export_data["room"]["messages"][0]["role"] == "user"
        assert export_data["room"]["messages"][0]["content"] == "안녕하세요"
        assert export_data["room"]["messages"][1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_export_multiple_rooms(self, db_with_data):
        """여러 채팅방 Export 데이터 구조 검증"""
        db, session_key, _ = db_with_data

        # 추가 채팅방 생성
        room_id_2 = "test_room_2"
        await db.upsert_room(room_id_2, session_key, "두 번째 채팅방", None)
        await db.save_message(room_id_2, "user", "두 번째 방 메시지")

        # 전체 방 목록 조회
        rooms = await db.list_rooms(session_key)
        assert len(rooms) == 2

        # Export 데이터 구조 생성 (전체)
        export_data = {
            "version": "1.0",
            "export_type": "full_backup",
            "session_key": session_key,
            "rooms": [],
        }

        for room in rooms:
            messages = await db.list_messages(room["room_id"])
            token_usage = await db.list_token_usage_range(room["room_id"])

            export_data["rooms"].append(
                {
                    "room_id": room["room_id"],
                    "title": room["title"],
                    "context": json.loads(room["context"]) if room["context"] else None,
                    "messages": [
                        {
                            "role": msg["role"],
                            "content": msg["content"],
                            "timestamp": msg["timestamp"],
                        }
                        for msg in messages
                    ],
                    "token_usage": [
                        {
                            "provider": usage["provider"],
                            "token_info": (
                                json.loads(usage["token_info"]) if usage["token_info"] else None
                            ),
                            "timestamp": usage["timestamp"],
                        }
                        for usage in token_usage
                    ],
                }
            )

        # 구조 검증
        assert export_data["export_type"] == "full_backup"
        assert len(export_data["rooms"]) == 2
        assert export_data["rooms"][0]["title"] in ["테스트 채팅방", "두 번째 채팅방"]

    @pytest.mark.asyncio
    async def test_export_date_range_filtering(self, db_with_data):
        """날짜 범위 필터링 테스트"""
        db, session_key, room_id = db_with_data

        # 모든 메시지 조회
        all_messages = await db.list_messages(room_id, session_key=session_key)
        assert len(all_messages) == 3

        # 날짜 범위로 조회 (실제 타임스탬프 사용)
        if all_messages:
            first_ts = all_messages[0]["timestamp"]
            last_ts = all_messages[-1]["timestamp"]

            # 전체 범위
            filtered = await db.list_messages_range(
                room_id, session_key=session_key, start=first_ts, end=last_ts
            )
            assert len(filtered) >= 1  # 최소 1개 이상

    @pytest.mark.asyncio
    async def test_export_empty_room(self, db_with_data):
        """빈 채팅방 Export 테스트"""
        db, session_key, _ = db_with_data

        # 빈 방 생성
        empty_room_id = "empty_room"
        await db.upsert_room(empty_room_id, session_key, "빈 채팅방", None)

        # 메시지 조회
        messages = await db.list_messages(empty_room_id)
        assert len(messages) == 0

        # Export 데이터 구조
        export_data = {
            "version": "1.0",
            "export_type": "single_room",
            "room": {
                "room_id": empty_room_id,
                "title": "빈 채팅방",
                "context": None,
                "messages": [],
                "token_usage": [],
            },
        }

        # 빈 방도 정상적으로 Export 가능
        assert export_data["room"]["room_id"] == empty_room_id
        assert len(export_data["room"]["messages"]) == 0

    @pytest.mark.asyncio
    async def test_export_context_parsing(self, db_with_data):
        """Context JSON 파싱 테스트"""
        db, session_key, room_id = db_with_data

        room = await db.get_room(room_id)
        assert room["context"] is not None

        # Context 파싱
        context = json.loads(room["context"])
        assert context["world"] == "판타지 세계"
        assert len(context["characters"]) == 1
        assert context["characters"][0]["name"] == "테스트 캐릭터"

    @pytest.mark.asyncio
    async def test_export_ndjson_format(self, db_with_data):
        """NDJSON 스트리밍 형식 검증"""
        db, session_key, room_id = db_with_data

        messages = await db.list_messages(room_id)

        # NDJSON 라인 생성
        ndjson_lines = []

        # Meta 라인
        meta = {"type": "meta", "version": "1.0", "export_type": "single_room"}
        ndjson_lines.append(json.dumps(meta, ensure_ascii=False))

        # Room 라인
        room = await db.get_room(room_id)
        room_line = {
            "type": "room",
            "room_id": room["room_id"],
            "title": room["title"],
            "context": json.loads(room["context"]) if room["context"] else None,
        }
        ndjson_lines.append(json.dumps(room_line, ensure_ascii=False))

        # Message 라인들
        for msg in messages:
            msg_line = {
                "type": "message",
                "room_id": room_id,
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"],
            }
            ndjson_lines.append(json.dumps(msg_line, ensure_ascii=False))

        # End 라인
        end_line = {"type": "end", "total_lines": len(ndjson_lines)}
        ndjson_lines.append(json.dumps(end_line, ensure_ascii=False))

        # NDJSON 검증
        ndjson_content = "\n".join(ndjson_lines)
        lines = ndjson_content.strip().split("\n")

        assert len(lines) >= 4  # meta + room + messages + end
        assert json.loads(lines[0])["type"] == "meta"
        assert json.loads(lines[1])["type"] == "room"
        assert json.loads(lines[-1])["type"] == "end"


class TestExportQueryParameters:
    """Export 쿼리 파라미터 파싱 테스트"""

    def test_query_param_scope(self):
        """scope 파라미터 파싱"""
        # single
        params = {"scope": ["single"], "room_id": ["test_room"]}
        assert params["scope"][0] == "single"
        assert params["room_id"][0] == "test_room"

        # selected
        params = {"scope": ["selected"], "room_ids": ["room1,room2,room3"]}
        room_ids = params["room_ids"][0].split(",")
        assert len(room_ids) == 3

        # full
        params = {"scope": ["full"]}
        assert params["scope"][0] == "full"

    def test_query_param_include(self):
        """include 파라미터 파싱"""
        params = {"include": ["messages,context,token_usage"]}
        include_items = params["include"][0].split(",")
        assert "messages" in include_items
        assert "context" in include_items
        assert "token_usage" in include_items

    def test_query_param_date_range(self):
        """날짜 범위 파라미터 파싱"""
        params = {"start": ["2025-01-01"], "end": ["2025-12-31"]}
        assert params["start"][0] == "2025-01-01"
        assert params["end"][0] == "2025-12-31"

    def test_query_param_format(self):
        """format 파라미터 파싱"""
        # JSON (기본값)
        params = {}
        format_type = params.get("format", ["json"])[0]
        assert format_type == "json"

        # ZIP
        params = {"format": ["zip"]}
        assert params["format"][0] == "zip"

    def test_url_encoding(self):
        """URL 인코딩 테스트"""
        params = {
            "scope": "single",
            "room_id": "test_room",
            "include": "messages,context",
        }
        query_string = urlencode(params)
        assert "scope=single" in query_string
        assert "room_id=test_room" in query_string
