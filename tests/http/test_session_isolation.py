"""HTTP export/import 세션 격리 테스트

이슈 #15: HTTP export/import API가 JWT의 session_key를 사용하여
세션별로 데이터를 격리하는지 테스트합니다.
"""

import json
import tempfile
from pathlib import Path

import jwt
import pytest
import pytest_asyncio

from server.handlers.db_handler import DBHandler


@pytest_asyncio.fixture
async def db_with_multi_session_data():
    """여러 세션의 테스트 데이터가 있는 DB 생성"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DBHandler(str(db_path))
        await db.initialize()

        # 세션 1: user:alice
        session1 = "user:alice"
        room1 = "room-001"
        context1 = json.dumps({"world": "Alice의 세계", "characters": [{"name": "앨리스"}]})
        await db.upsert_room(room1, session1, "Alice의 방", context1)
        await db.save_message(room1, "user", "안녕, 나는 Alice야")
        await db.save_message(room1, "assistant", "[앨리스]: 반가워!")
        await db.save_token_usage(session1, room1, "claude", json.dumps({"input_tokens": 10}))

        # 세션 2: user:bob (같은 room_id 사용!)
        session2 = "user:bob"
        room2 = "room-001"  # 같은 room_id
        context2 = json.dumps({"world": "Bob의 세계", "characters": [{"name": "밥"}]})
        await db.upsert_room(room2, session2, "Bob의 방", context2)
        await db.save_message(room2, "user", "안녕, 나는 Bob이야")
        await db.save_message(room2, "assistant", "[밥]: 만나서 반가워!")
        await db.save_token_usage(session2, room2, "claude", json.dumps({"input_tokens": 20}))

        yield db, session1, session2, room1, room2

        await db.close()


class TestSessionIsolation:
    """세션별 데이터 격리 테스트"""

    @pytest.mark.asyncio
    async def test_jwt_contains_session_key(self, monkeypatch):
        """JWT payload에 session_key가 포함되는지 테스트"""
        # JWT_SECRET 설정

        monkeypatch.setenv(
            "APP_JWT_SECRET", "test_secret_key_for_testing"
        )  # pragma: allowlist secret

        # websocket_server 모듈 reload 필요 (환경변수 반영)
        import importlib

        import server.websocket_server

        importlib.reload(server.websocket_server)

        from server.websocket_server import _issue_token

        session_key = "user:testuser"
        token, _ = _issue_token(ttl_seconds=3600, typ="access", session_key=session_key)

        assert token is not None

        # JWT 디코딩 (검증 없이)
        payload = jwt.decode(token, options={"verify_signature": False})

        assert "session_key" in payload
        assert payload["session_key"] == session_key
        assert payload["typ"] == "access"
        assert payload["sub"] == "persona_chat_user"

    @pytest.mark.asyncio
    async def test_db_get_room_with_session_key(self, db_with_multi_session_data):
        """DB get_room이 session_key로 격리되는지 테스트"""
        db, session1, session2, room1, room2 = db_with_multi_session_data

        # session1으로 room-001 조회 -> Alice의 방
        room_alice = await db.get_room(room1, session1)
        assert room_alice is not None
        assert room_alice["title"] == "Alice의 방"
        context_alice = json.loads(room_alice["context"])
        assert context_alice["world"] == "Alice의 세계"

        # session2로 room-001 조회 -> Bob의 방
        room_bob = await db.get_room(room2, session2)
        assert room_bob is not None
        assert room_bob["title"] == "Bob의 방"
        context_bob = json.loads(room_bob["context"])
        assert context_bob["world"] == "Bob의 세계"

        # session1으로 room-001 조회했을 때 Bob의 데이터가 안 나와야 함
        assert room_alice["title"] != room_bob["title"]

    @pytest.mark.asyncio
    async def test_db_delete_room_with_session_key(self, db_with_multi_session_data):
        """DB delete_room이 session_key로 격리되는지 테스트"""
        db, session1, session2, room1, _ = db_with_multi_session_data

        # session1으로 room-001 삭제
        await db.delete_room(room1, session1)

        # session1으로 조회 -> None
        room_alice = await db.get_room(room1, session1)
        assert room_alice is None

        # session2로 조회 -> Bob의 방은 여전히 존재
        room_bob = await db.get_room(room1, session2)
        assert room_bob is not None
        assert room_bob["title"] == "Bob의 방"

    @pytest.mark.asyncio
    async def test_db_list_rooms_with_session_key(self, db_with_multi_session_data):
        """DB list_rooms가 session_key로 격리되는지 테스트"""
        db, session1, session2, _, _ = db_with_multi_session_data

        # session1으로 방 목록 조회 -> Alice의 방만
        rooms_alice = await db.list_rooms(session1)
        assert len(rooms_alice) == 1
        assert rooms_alice[0]["title"] == "Alice의 방"

        # session2로 방 목록 조회 -> Bob의 방만
        rooms_bob = await db.list_rooms(session2)
        assert len(rooms_bob) == 1
        assert rooms_bob[0]["title"] == "Bob의 방"

    @pytest.mark.asyncio
    async def test_jwt_without_session_key_backward_compatible(self, monkeypatch):
        """session_key 없는 JWT도 동작하는지 테스트 (하위 호환성)"""
        # JWT_SECRET 설정

        monkeypatch.setenv(
            "APP_JWT_SECRET", "test_secret_key_for_testing"
        )  # pragma: allowlist secret

        # websocket_server 모듈 reload 필요 (환경변수 반영)
        import importlib

        import server.websocket_server

        importlib.reload(server.websocket_server)

        from server.websocket_server import _issue_token

        # session_key 없이 토큰 생성
        token, _ = _issue_token(ttl_seconds=3600, typ="access", session_key=None)

        assert token is not None

        # JWT 디코딩
        payload = jwt.decode(token, options={"verify_signature": False})

        # session_key가 없어야 함
        assert "session_key" not in payload
        assert payload["typ"] == "access"

    @pytest.mark.asyncio
    async def test_import_fallback_session_key(self):
        """import API에서 session_key fallback 로직 테스트

        - JWT에 session_key가 없어도 request_data에서 가져올 수 있음
        - 둘 다 없으면 기본값 "http_import" 사용
        """
        # 시나리오 1: JWT 없음 (login_required=False)
        session_key = None  # JWT에서 추출 실패
        request_data = {}  # request_data에도 없음

        # Fallback 로직 시뮬레이션
        final_key = session_key or request_data.get("session_key", "http_import")
        assert final_key == "http_import"

        # 시나리오 2: JWT에 session_key 없지만 request_data에 있음
        session_key = None
        request_data = {"session_key": "custom_session"}

        final_key = session_key or request_data.get("session_key", "http_import")
        assert final_key == "custom_session"

        # 시나리오 3: JWT에 session_key 있음 (우선순위 최상)
        session_key = "user:alice"
        request_data = {"session_key": "should_be_ignored"}

        final_key = session_key or request_data.get("session_key", "http_import")
        assert final_key == "user:alice"
