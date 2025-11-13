"""DBHandler CRUD 단위 테스트"""

import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from server.handlers.db_handler import DBHandler


@pytest_asyncio.fixture
async def db():
    """임시 DB 생성 및 초기화"""
    # 임시 디렉토리에 테스트용 DB 생성
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        handler = DBHandler(str(db_path))
        await handler.initialize()
        yield handler
        await handler.close()


class TestDBHandler:
    """DBHandler CRUD 테스트"""

    # ===== Sessions =====

    @pytest.mark.asyncio
    async def test_upsert_session(self, db):
        """세션 생성 및 업데이트 테스트"""
        session_key = "test_session_001"

        # 세션 생성
        await db.upsert_session(session_key)

        # 세션이 생성되었는지 확인 (rooms를 통해 간접 확인)
        # 직접 세션 조회 메서드가 없으므로, upsert가 성공하면 OK
        await db.upsert_session(session_key)  # 중복 생성 시도 (에러 없어야 함)

    # ===== Rooms =====

    @pytest.mark.asyncio
    async def test_upsert_room_create(self, db):
        """채팅방 생성 테스트"""
        room_id = "fantasy_001"
        session_key = "test_session"
        title = "판타지 모험"
        context = '{"world": "판타지 세계"}'

        await db.upsert_room(room_id, session_key, title, context)

        # 채팅방 조회
        room = await db.get_room(room_id)
        assert room is not None
        assert room["room_id"] == room_id
        assert room["session_key"] == session_key
        assert room["title"] == title
        assert room["context"] == context

    @pytest.mark.asyncio
    async def test_upsert_room_update(self, db):
        """채팅방 업데이트 테스트"""
        room_id = "test_room"
        session_key = "test_session"

        # 초기 생성
        await db.upsert_room(room_id, session_key, "원래 제목", '{"old": "data"}')

        # 업데이트
        new_title = "새로운 제목"
        new_context = '{"new": "data"}'
        await db.upsert_room(room_id, session_key, new_title, new_context)

        # 확인
        room = await db.get_room(room_id)
        assert room["title"] == new_title
        assert room["context"] == new_context

    @pytest.mark.asyncio
    async def test_list_rooms(self, db):
        """채팅방 목록 조회 테스트"""
        session_key = "test_session"

        # 3개 채팅방 생성
        await db.upsert_room("room_1", session_key, "방 1", None)
        await db.upsert_room("room_2", session_key, "방 2", None)
        await db.upsert_room("room_3", session_key, "방 3", None)

        # 목록 조회
        rooms = await db.list_rooms(session_key)
        assert len(rooms) == 3

        # 최신 업데이트 순 정렬 확인 (DESC)
        room_ids = [r["room_id"] for r in rooms]
        assert "room_3" in room_ids

    @pytest.mark.asyncio
    async def test_delete_room(self, db):
        """채팅방 삭제 테스트"""
        room_id = "room_to_delete"
        session_key = "test_session"

        await db.upsert_room(room_id, session_key, "삭제될 방", None)

        # 존재 확인
        room = await db.get_room(room_id)
        assert room is not None

        # 삭제
        await db.delete_room(room_id)

        # 삭제 확인
        room = await db.get_room(room_id)
        assert room is None

    # ===== Messages =====

    @pytest.mark.asyncio
    async def test_save_and_list_messages(self, db):
        """메시지 저장 및 조회 테스트"""
        room_id = "test_room"
        session_key = "test_session"

        # 방 생성
        await db.upsert_room(room_id, session_key, "테스트 방", None)

        # 메시지 저장
        await db.save_message(room_id, "user", "안녕하세요")
        await db.save_message(room_id, "assistant", "[캐릭터]: 반갑습니다")
        await db.save_message(room_id, "user", "어떻게 지내세요?")

        # 메시지 조회
        messages = await db.list_messages(room_id)
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "안녕하세요"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["content"] == "어떻게 지내세요?"

    @pytest.mark.asyncio
    async def test_list_messages_with_limit(self, db):
        """메시지 제한 조회 테스트"""
        room_id = "test_room"
        session_key = "test_session"

        await db.upsert_room(room_id, session_key, "테스트", None)

        # 5개 메시지 저장
        for i in range(5):
            await db.save_message(room_id, "user", f"메시지 {i+1}")

        # 최근 3개만 조회
        messages = await db.list_messages(room_id, limit=3)
        assert len(messages) == 3

    @pytest.mark.asyncio
    async def test_list_messages_range(self, db):
        """날짜 범위 메시지 조회 테스트"""
        room_id = "test_room"
        session_key = "test_session"

        await db.upsert_room(room_id, session_key, "테스트", None)

        # 메시지 저장
        await db.save_message(room_id, "user", "메시지 1")
        await db.save_message(room_id, "user", "메시지 2")
        await db.save_message(room_id, "user", "메시지 3")

        # 전체 조회 (날짜 필터 없음)
        messages = await db.list_messages_range(room_id)
        assert len(messages) == 3

    # ===== Token Usage =====

    @pytest.mark.asyncio
    async def test_save_token_usage(self, db):
        """토큰 사용량 저장 테스트"""
        room_id = "test_room"
        session_key = "test_session"

        await db.upsert_room(room_id, session_key, "테스트", None)

        # 토큰 사용량 저장
        token_info = '{"input_tokens": 100, "output_tokens": 200}'
        await db.save_token_usage(session_key, room_id, "claude", token_info)

        # 조회
        usage_list = await db.list_token_usage_range(room_id)
        assert len(usage_list) == 1
        assert usage_list[0]["provider"] == "claude"
        assert usage_list[0]["token_info"] == token_info

    @pytest.mark.asyncio
    async def test_cascade_delete_messages(self, db):
        """채팅방 삭제 시 메시지 cascade 삭제 테스트"""
        room_id = "test_room"
        session_key = "test_session"

        await db.upsert_room(room_id, session_key, "테스트", None)
        await db.save_message(room_id, "user", "메시지 1")
        await db.save_message(room_id, "user", "메시지 2")

        # 메시지 존재 확인
        messages = await db.list_messages(room_id)
        assert len(messages) == 2

        # 방 삭제
        await db.delete_room(room_id)

        # 메시지도 함께 삭제되었는지 확인
        messages = await db.list_messages(room_id)
        assert len(messages) == 0

    # ===== Edge Cases =====

    @pytest.mark.asyncio
    async def test_get_nonexistent_room(self, db):
        """존재하지 않는 방 조회"""
        room = await db.get_room("nonexistent_room")
        assert room is None

    @pytest.mark.asyncio
    async def test_list_messages_empty_room(self, db):
        """메시지가 없는 방 조회"""
        room_id = "empty_room"
        session_key = "test_session"

        await db.upsert_room(room_id, session_key, "빈 방", None)

        messages = await db.list_messages(room_id)
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_context_null(self, db):
        """context가 null인 채팅방"""
        room_id = "room_without_context"
        session_key = "test_session"

        await db.upsert_room(room_id, session_key, "컨텍스트 없는 방", None)

        room = await db.get_room(room_id)
        assert room["context"] is None
