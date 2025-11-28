"""DBHandler CRUD 단위 테스트 (user_id 기반)"""

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

        # 테스트용 사용자 생성
        await handler.create_user("testuser", "test@example.com", "password_hash")
        await handler.approve_user(1, 1)  # user_id=1을 승인

        yield handler
        await handler.close()


class TestDBHandler:
    """DBHandler CRUD 테스트 (user_id 기반)"""

    # ===== Sessions 테스트 제거 (user_id 기반 시스템에서는 sessions 테이블 없음) =====

    # ===== Rooms =====

    @pytest.mark.asyncio
    async def test_upsert_room_create(self, db):
        """채팅방 생성 테스트"""
        room_id = "fantasy_001"
        user_id = 1  # 테스트용 사용자
        title = "판타지 모험"
        context = '{"world": "판타지 세계"}'

        await db.upsert_room(room_id, user_id, title, context)

        # 채팅방 조회
        room = await db.get_room(room_id, user_id)
        assert room is not None
        assert room["room_id"] == room_id
        assert room["user_id"] == user_id
        assert room["title"] == title
        assert room["context"] == context

    @pytest.mark.asyncio
    async def test_upsert_room_update(self, db):
        """채팅방 업데이트 테스트"""
        room_id = "test_room"
        user_id = 1

        # 초기 생성
        await db.upsert_room(room_id, user_id, "원래 제목", '{"old": "data"}')

        # 업데이트
        new_title = "새로운 제목"
        new_context = '{"new": "data"}'
        await db.upsert_room(room_id, user_id, new_title, new_context)

        # 확인
        room = await db.get_room(room_id, user_id)
        assert room["title"] == new_title
        assert room["context"] == new_context

    @pytest.mark.asyncio
    async def test_upsert_room_with_provider_sessions(self, db):
        """provider_sessions 저장 및 조회 테스트 (서버 재시작 후 세션 복원용)"""
        room_id = "session_test_room"
        user_id = 1

        # provider_sessions 포함하여 방 생성
        provider_sessions = '{"claude": "abc-123", "gemini": "def-456"}'
        await db.upsert_room(
            room_id, user_id, "세션 테스트 방", '{"test": true}', provider_sessions
        )

        # 조회 확인
        room = await db.get_room(room_id, user_id)
        assert room is not None
        assert room["provider_sessions"] == provider_sessions

    @pytest.mark.asyncio
    async def test_upsert_room_provider_sessions_update(self, db):
        """provider_sessions 업데이트 테스트"""
        room_id = "session_update_room"
        user_id = 1

        # 초기 생성 (provider_sessions 없이)
        await db.upsert_room(room_id, user_id, "방 제목", "{}")

        room = await db.get_room(room_id, user_id)
        assert room["provider_sessions"] == "{}"

        # provider_sessions 업데이트
        new_sessions = '{"claude": "new-session-id"}'
        await db.upsert_room(room_id, user_id, "방 제목", "{}", new_sessions)

        room = await db.get_room(room_id, user_id)
        assert room["provider_sessions"] == new_sessions

    @pytest.mark.asyncio
    async def test_upsert_room_provider_sessions_preserved_on_null(self, db):
        """provider_sessions가 None으로 전달되면 기존 값 유지 테스트"""
        room_id = "session_preserve_room"
        user_id = 1

        # 초기 생성 (provider_sessions 있음)
        initial_sessions = '{"claude": "keep-this"}'
        await db.upsert_room(room_id, user_id, "방 제목", "{}", initial_sessions)

        # provider_sessions 없이 업데이트 (기존 값 유지되어야 함)
        await db.upsert_room(room_id, user_id, "새 제목", '{"new": true}', None)

        room = await db.get_room(room_id, user_id)
        assert room["title"] == "새 제목"
        # COALESCE로 기존 값 유지
        assert room["provider_sessions"] == initial_sessions

    @pytest.mark.asyncio
    async def test_list_rooms(self, db):
        """채팅방 목록 조회 테스트"""
        user_id = 1

        # 3개 채팅방 생성
        await db.upsert_room("room_1", user_id, "방 1", None)
        await db.upsert_room("room_2", user_id, "방 2", None)
        await db.upsert_room("room_3", user_id, "방 3", None)

        # 목록 조회
        rooms = await db.list_rooms(user_id)
        assert len(rooms) == 3

        # 최신 업데이트 순 정렬 확인 (DESC)
        room_ids = [r["room_id"] for r in rooms]
        assert "room_3" in room_ids

    @pytest.mark.asyncio
    async def test_delete_room(self, db):
        """채팅방 삭제 테스트"""
        room_id = "room_to_delete"
        user_id = 1

        await db.upsert_room(room_id, user_id, "삭제될 방", None)

        # 존재 확인
        room = await db.get_room(room_id, user_id)
        assert room is not None

        # 삭제
        await db.delete_room(room_id, user_id)

        # 삭제 확인
        room = await db.get_room(room_id, user_id)
        assert room is None

    # ===== Messages =====

    @pytest.mark.asyncio
    async def test_save_and_list_messages(self, db):
        """메시지 저장 및 조회 테스트"""
        room_id = "test_room"
        user_id = 1

        # 방 생성
        await db.upsert_room(room_id, user_id, "테스트 방", None)

        # 메시지 저장
        await db.save_message(room_id, "user", "안녕하세요", user_id)
        await db.save_message(room_id, "assistant", "[캐릭터]: 반갑습니다", user_id)
        await db.save_message(room_id, "user", "어떻게 지내세요?", user_id)

        # 메시지 조회
        messages = await db.list_messages(room_id, user_id)
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "안녕하세요"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["content"] == "어떻게 지내세요?"

    @pytest.mark.asyncio
    async def test_list_messages_with_limit(self, db):
        """메시지 제한 조회 테스트"""
        room_id = "test_room"
        user_id = 1

        await db.upsert_room(room_id, user_id, "테스트", None)

        # 5개 메시지 저장
        for i in range(5):
            await db.save_message(room_id, "user", f"메시지 {i+1}", user_id)

        # 최근 3개만 조회
        messages = await db.list_messages(room_id, user_id, limit=3)
        assert len(messages) == 3

    @pytest.mark.asyncio
    async def test_list_messages_range(self, db):
        """날짜 범위 메시지 조회 테스트"""
        room_id = "test_room"
        user_id = 1

        await db.upsert_room(room_id, user_id, "테스트", None)

        # 메시지 저장
        await db.save_message(room_id, "user", "메시지 1", user_id)
        await db.save_message(room_id, "user", "메시지 2", user_id)
        await db.save_message(room_id, "user", "메시지 3", user_id)

        # 전체 조회 (날짜 필터 없음)
        messages = await db.list_messages_range(room_id, user_id=user_id)
        assert len(messages) == 3

    # ===== Token Usage =====

    @pytest.mark.asyncio
    async def test_save_token_usage(self, db):
        """토큰 사용량 저장 테스트"""
        room_id = "test_room"
        user_id = 1

        await db.upsert_room(room_id, user_id, "테스트", None)

        # 토큰 사용량 저장
        token_info = {"input_tokens": 100, "output_tokens": 200}
        await db.save_token_usage(user_id, room_id, "claude", token_info)

        # 조회
        usage_list = await db.list_token_usage_range(room_id, user_id=user_id)
        assert len(usage_list) == 1
        assert usage_list[0]["provider"] == "claude"

    @pytest.mark.asyncio
    async def test_cascade_delete_messages(self, db):
        """채팅방 삭제 시 메시지 cascade 삭제 테스트"""
        room_id = "test_room"
        user_id = 1

        await db.upsert_room(room_id, user_id, "테스트", None)
        await db.save_message(room_id, "user", "메시지 1", user_id)
        await db.save_message(room_id, "user", "메시지 2", user_id)

        # 메시지 존재 확인
        messages = await db.list_messages(room_id, user_id)
        assert len(messages) == 2

        # 방 삭제
        await db.delete_room(room_id, user_id)

        # 메시지도 함께 삭제되었는지 확인
        messages = await db.list_messages(room_id, user_id)
        assert len(messages) == 0

    # ===== Edge Cases =====

    @pytest.mark.asyncio
    async def test_get_nonexistent_room(self, db):
        """존재하지 않는 방 조회"""
        user_id = 1
        room = await db.get_room("nonexistent_room", user_id)
        assert room is None

    @pytest.mark.asyncio
    async def test_list_messages_empty_room(self, db):
        """메시지가 없는 방 조회"""
        room_id = "empty_room"
        user_id = 1

        await db.upsert_room(room_id, user_id, "빈 방", None)

        messages = await db.list_messages(room_id, user_id)
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_context_null(self, db):
        """context가 null인 채팅방"""
        room_id = "room_without_context"
        user_id = 1

        await db.upsert_room(room_id, user_id, "컨텍스트 없는 방", None)

        room = await db.get_room(room_id, user_id)
        assert room["context"] is None
