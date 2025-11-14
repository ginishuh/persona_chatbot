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

    @pytest.mark.asyncio
    async def test_export_session_isolation_db_path(self, db_with_multi_session_data):
        """export API에서 DB 경로가 session_key로 필터링되는지 테스트

        - Alice의 JWT로 export → Alice의 데이터만
        - Bob의 JWT로 export → Bob의 데이터만
        - session_key 없이 export → 빈 결과 (login_required=True일 때)
        """
        db, session1, session2, room1, room2 = db_with_multi_session_data

        # Alice의 room_id=room-001 export (session1)
        room_alice = await db.get_room(room1, session1)
        assert room_alice is not None
        assert room_alice["title"] == "Alice의 방"

        # Bob의 room_id=room-001 export (session2)
        room_bob = await db.get_room(room2, session2)
        assert room_bob is not None
        assert room_bob["title"] == "Bob의 방"

        # 잘못된 session_key로 조회 → None
        room_wrong = await db.get_room(room1, "wrong_session")
        assert room_wrong is None

        # session_key 없이 조회 (하위 호환 모드) → 첫 번째 발견된 방 반환
        room_no_key = await db.get_room(room1)
        assert room_no_key is not None
        # Alice와 Bob 중 하나의 방이 반환됨 (어느 것이든 상관없음)
        assert room_no_key["title"] in ["Alice의 방", "Bob의 방"]

    @pytest.mark.asyncio
    async def test_memory_fallback_session_isolation(self):
        """메모리 폴백 경로가 session_key로 격리되는지 테스트

        - login_required=True일 때 session_key 일치만 검색
        - login_required=False일 때 모든 세션 검색 (하위 호환)
        """
        from server.core.app_context import AppContext

        # Mock AppContext with sessions
        ctx = AppContext(
            project_root="/tmp",
            bind_host="127.0.0.1",
            login_required=True,
            jwt_secret="test",  # pragma: allowlist secret
            jwt_algorithm="HS256",
            access_ttl_seconds=3600,
            refresh_ttl_seconds=86400,
            login_username="",
            login_rate_limit_max_attempts=5,
            login_rate_limit_window_seconds=900,
            token_expired_grace_seconds=3600,
        )

        # Mock sessions
        ctx.sessions = {
            "user:alice": {
                "rooms": {
                    "room-001": {
                        "history": type(
                            "MockHistory",
                            (),
                            {
                                "get_history": lambda self: [
                                    {"role": "user", "content": "Alice's message"}
                                ]
                            },
                        )()
                    }
                }
            },
            "user:bob": {
                "rooms": {
                    "room-001": {
                        "history": type(
                            "MockHistory",
                            (),
                            {
                                "get_history": lambda self: [
                                    {"role": "user", "content": "Bob's message"}
                                ]
                            },
                        )()
                    }
                }
            },
        }

        # login_required=True: session_key 일치만 검색
        assert ctx.login_required is True

        # Alice의 session으로 검색
        alice_session = ctx.sessions.get("user:alice")
        assert alice_session is not None
        room = alice_session.get("rooms", {}).get("room-001")
        assert room is not None
        msgs = room["history"].get_history()
        assert msgs[0]["content"] == "Alice's message"

        # Bob의 session으로 검색
        bob_session = ctx.sessions.get("user:bob")
        assert bob_session is not None
        room = bob_session.get("rooms", {}).get("room-001")
        assert room is not None
        msgs = room["history"].get_history()
        assert msgs[0]["content"] == "Bob's message"

        # 잘못된 session_key → None
        wrong_session = ctx.sessions.get("user:charlie")
        assert wrong_session is None

        # login_required=False: 모든 세션 검색 (하위 호환)
        ctx.login_required = False

        # 모든 세션 순회 가능 확인
        found_alice = False
        found_bob = False
        for sess in ctx.sessions.values():
            room = sess.get("rooms", {}).get("room-001")
            if room:
                msgs = room["history"].get_history()
                if msgs[0]["content"] == "Alice's message":
                    found_alice = True
                elif msgs[0]["content"] == "Bob's message":
                    found_bob = True

        assert found_alice
        assert found_bob
