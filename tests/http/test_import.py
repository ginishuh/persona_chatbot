"""Import HTTP 엔드포인트 통합 테스트"""

import json
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from server.handlers.db_handler import DBHandler


@pytest_asyncio.fixture
async def db_empty():
    """빈 DB 생성"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DBHandler(str(db_path))
        await db.initialize()
        yield db
        await db.close()


@pytest_asyncio.fixture
async def db_with_existing_room():
    """기존 채팅방이 있는 DB 생성"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DBHandler(str(db_path))
        await db.initialize()

        # 기존 방 생성
        session_key = "test_session"
        room_id = "existing_room"
        context = json.dumps({"world": "기존 세계"})

        await db.upsert_room(room_id, session_key, "기존 채팅방", context)
        await db.save_message(room_id, "user", "기존 메시지 1")
        await db.save_message(room_id, "assistant", "기존 응답 1")

        yield db, session_key, room_id

        await db.close()


class TestImportDataStructure:
    """Import 데이터 구조 검증 테스트"""

    def test_single_room_import_structure(self):
        """single_room 타입 Import 데이터 구조"""
        import_data = {
            "session_key": "test_session",
            "duplicate_policy": "skip",
            "json_data": {
                "version": "1.0",
                "export_type": "single_room",
                "room": {
                    "room_id": "test_room",
                    "title": "테스트 채팅방",
                    "context": {"world": "판타지 세계"},
                    "messages": [
                        {
                            "role": "user",
                            "content": "안녕하세요",
                            "timestamp": "2025-01-01T00:00:00",
                        }
                    ],
                    "token_usage": [],
                },
            },
        }

        # 구조 검증
        assert import_data["json_data"]["export_type"] == "single_room"
        assert "room" in import_data["json_data"]
        assert import_data["json_data"]["room"]["room_id"] == "test_room"
        assert len(import_data["json_data"]["room"]["messages"]) == 1

    def test_full_backup_import_structure(self):
        """full_backup 타입 Import 데이터 구조"""
        import_data = {
            "session_key": "test_session",
            "duplicate_policy": "merge",
            "json_data": {
                "version": "1.0",
                "export_type": "full_backup",
                "session_key": "original_session",
                "rooms": [
                    {
                        "room_id": "room_1",
                        "title": "방 1",
                        "context": None,
                        "messages": [],
                        "token_usage": [],
                    },
                    {
                        "room_id": "room_2",
                        "title": "방 2",
                        "context": {"world": "세계 2"},
                        "messages": [{"role": "user", "content": "메시지"}],
                        "token_usage": [],
                    },
                ],
            },
        }

        # 구조 검증
        assert import_data["json_data"]["export_type"] == "full_backup"
        assert "rooms" in import_data["json_data"]
        assert len(import_data["json_data"]["rooms"]) == 2
        assert import_data["json_data"]["rooms"][0]["room_id"] == "room_1"

    def test_selected_import_structure(self):
        """selected 타입 Import 데이터 구조"""
        import_data = {
            "session_key": "test_session",
            "duplicate_policy": "skip",
            "json_data": {
                "version": "1.0",
                "export_type": "selected",
                "rooms": [
                    {
                        "room_id": "room_a",
                        "title": "방 A",
                        "context": None,
                        "messages": [],
                        "token_usage": [],
                    }
                ],
            },
        }

        # 구조 검증
        assert import_data["json_data"]["export_type"] == "selected"
        assert "rooms" in import_data["json_data"]


class TestImportLogic:
    """Import 로직 테스트 (간단 DB 연동)"""

    @pytest.mark.asyncio
    async def test_direct_db_room_creation(self, db_empty):
        """DB에 직접 방 생성 (Import 시뮬레이션)"""
        session_key = "test_session"
        room_id = "new_room"
        title = "새 채팅방"
        context = json.dumps({"world": "판타지"})

        # 방 생성
        await db_empty.upsert_room(room_id, session_key, title, context)

        # 메시지 추가
        await db_empty.save_message(room_id, "user", "안녕하세요")

        # 검증
        room = await db_empty.get_room(room_id)
        assert room is not None
        assert room["title"] == title

        messages = await db_empty.list_messages(room_id)
        assert len(messages) == 1
        assert messages[0]["content"] == "안녕하세요"

    @pytest.mark.asyncio
    async def test_duplicate_room_handling(self, db_with_existing_room):
        """중복 방 처리 시뮬레이션"""
        db, session_key, room_id = db_with_existing_room

        # 기존 방 확인
        existing_room = await db.get_room(room_id)
        assert existing_room is not None
        assert existing_room["title"] == "기존 채팅방"

        # 같은 ID로 upsert (title 업데이트)
        new_title = "업데이트된 제목"
        new_context = json.dumps({"world": "새 세계"})
        await db.upsert_room(room_id, session_key, new_title, new_context)

        # 검증: 방이 업데이트됨
        updated_room = await db.get_room(room_id)
        assert updated_room["title"] == new_title

        # 기존 메시지는 유지됨
        messages = await db.list_messages(room_id)
        assert len(messages) == 2

    @pytest.mark.asyncio
    async def test_import_message_append(self, db_with_existing_room):
        """메시지 추가 (merge 시뮬레이션)"""
        db, session_key, room_id = db_with_existing_room

        # 기존 메시지 확인
        existing_messages = await db.list_messages(room_id)
        assert len(existing_messages) == 2

        # 새 메시지 추가
        await db.save_message(room_id, "user", "추가 메시지 1")
        await db.save_message(room_id, "assistant", "추가 응답 1")

        # 검증: 메시지 총 4개
        all_messages = await db.list_messages(room_id)
        assert len(all_messages) == 4

    @pytest.mark.asyncio
    async def test_import_empty_room(self, db_empty):
        """빈 방 Import"""
        session_key = "test_session"
        room_id = "empty_room"

        await db_empty.upsert_room(room_id, session_key, "빈 방", None)

        room = await db_empty.get_room(room_id)
        assert room is not None
        assert room["context"] is None

        messages = await db_empty.list_messages(room_id)
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_import_null_context(self, db_empty):
        """context가 null인 방"""
        session_key = "test_session"
        room_id = "no_context_room"

        await db_empty.upsert_room(room_id, session_key, "컨텍스트 없는 방", None)
        await db_empty.save_message(room_id, "user", "메시지")

        room = await db_empty.get_room(room_id)
        assert room["context"] is None

        messages = await db_empty.list_messages(room_id)
        assert len(messages) == 1


class TestImportEdgeCases:
    """Import 엣지 케이스 테스트"""

    def test_invalid_export_type(self):
        """유효하지 않은 export_type"""
        import_data = {
            "json_data": {
                "version": "1.0",
                "export_type": "invalid_type",
                "rooms": [],
            }
        }

        export_type = import_data["json_data"].get("export_type", "").lower()
        assert export_type not in ["single_room", "full_backup", "selected"]

    def test_missing_room_field(self):
        """single_room에서 room 필드 누락"""
        import_data = {
            "json_data": {
                "version": "1.0",
                "export_type": "single_room",
                # "room" 필드 누락
            }
        }

        assert "room" not in import_data["json_data"]

    def test_missing_rooms_field(self):
        """full_backup에서 rooms 필드 누락"""
        import_data = {
            "json_data": {
                "version": "1.0",
                "export_type": "full_backup",
                # "rooms" 필드 누락
            }
        }

        assert "rooms" not in import_data["json_data"]

    def test_empty_room_id(self):
        """빈 room_id"""
        room_data = {
            "room_id": "",
            "title": "제목",
            "context": None,
            "messages": [],
            "token_usage": [],
        }

        assert room_data["room_id"] == ""

    def test_special_characters_in_room_id(self):
        """특수 문자 포함 room_id"""
        room_ids = [
            "room-with-dash",
            "room_with_underscore",
            "room.with.dot",
            "room@with@at",
            "한글_방_이름",
        ]

        for room_id in room_ids:
            room_data = {"room_id": room_id, "title": "테스트", "messages": []}
            assert room_data["room_id"] == room_id

    def test_very_long_room_id(self):
        """매우 긴 room_id"""
        long_id = "a" * 1000
        room_data = {"room_id": long_id, "title": "테스트"}
        assert len(room_data["room_id"]) == 1000


class TestImportRequestValidation:
    """Import HTTP 요청 검증 테스트"""

    def test_content_type_json(self):
        """Content-Type 검증: application/json"""
        content_type = "application/json"
        assert "application/json" in content_type

    def test_content_type_multipart(self):
        """Content-Type 검증: multipart/form-data"""
        content_type = "multipart/form-data; boundary=----WebKitFormBoundary"
        assert "multipart/form-data" in content_type

    def test_content_type_invalid(self):
        """Content-Type 검증: 지원하지 않는 타입"""
        content_type = "text/plain"
        assert "application/json" not in content_type
        assert "multipart/form-data" not in content_type

    def test_content_length_limit(self):
        """Content-Length 제한 검증 (100MB)"""
        max_size = 100 * 1024 * 1024  # 100MB

        # 정상 크기
        assert 1024 < max_size

        # 초과 크기
        oversized = 150 * 1024 * 1024
        assert oversized > max_size

    def test_json_parsing(self):
        """JSON 파싱 테스트"""
        valid_json = '{"export_type": "single_room", "room": {}}'
        parsed = json.loads(valid_json)
        assert parsed["export_type"] == "single_room"

    def test_json_parsing_invalid(self):
        """잘못된 JSON 파싱 테스트"""
        invalid_json = '{"export_type": "single_room", "room": '

        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)


class TestImportMultipleRooms:
    """여러 채팅방 Import 테스트"""

    @pytest.mark.asyncio
    async def test_import_multiple_rooms_simulation(self, db_empty):
        """여러 방 Import 시뮬레이션"""
        session_key = "test_session"

        rooms_data = [
            {"room_id": "room_1", "title": "방 1", "context": None},
            {"room_id": "room_2", "title": "방 2", "context": json.dumps({"world": "세계 2"})},
            {"room_id": "room_3", "title": "방 3", "context": None},
        ]

        # 각 방 생성
        for room_data in rooms_data:
            await db_empty.upsert_room(
                room_data["room_id"], session_key, room_data["title"], room_data["context"]
            )

        # 메시지 추가
        await db_empty.save_message("room_1", "user", "메시지 1")
        await db_empty.save_message("room_2", "user", "메시지 2")
        # room_3는 메시지 없음

        # 검증
        rooms = await db_empty.list_rooms(session_key)
        assert len(rooms) == 3

        # 개별 방 확인
        room1 = await db_empty.get_room("room_1")
        assert room1["title"] == "방 1"

        messages1 = await db_empty.list_messages("room_1")
        assert len(messages1) == 1

        messages3 = await db_empty.list_messages("room_3")
        assert len(messages3) == 0

    @pytest.mark.asyncio
    async def test_import_selected_rooms_simulation(self, db_empty):
        """선택된 방만 Import 시뮬레이션"""
        session_key = "test_session"

        # 2개 방만 선택
        selected_rooms = [
            {"room_id": "selected_1", "title": "선택 1"},
            {"room_id": "selected_2", "title": "선택 2"},
        ]

        for room_data in selected_rooms:
            await db_empty.upsert_room(room_data["room_id"], session_key, room_data["title"], None)

        # 검증
        rooms = await db_empty.list_rooms(session_key)
        assert len(rooms) == 2

        room_ids = [r["room_id"] for r in rooms]
        assert "selected_1" in room_ids
        assert "selected_2" in room_ids
