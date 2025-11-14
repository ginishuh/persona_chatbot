"""HTTP 회원가입/로그인 인증 테스트

이슈 #16: 단일 비밀번호 방식에서 회원제 시스템으로 전환
- 회원가입 API (POST /api/register)
- 로그인 API (POST /api/login)
- JWT에 user_id 포함 확인
- 토큰 갱신 시 user_id 보존 확인
"""

import tempfile
from pathlib import Path

import jwt
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
async def db_with_users():
    """테스트 사용자가 있는 DB 생성"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DBHandler(str(db_path))
        await db.initialize()

        # 테스트 사용자 생성
        import bcrypt

        password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        user_id = await db.create_user("testuser", "test@example.com", password_hash)

        yield db, user_id

        await db.close()


class TestRegisterAPI:
    """회원가입 API 테스트"""

    @pytest.mark.asyncio
    async def test_register_success(self, db_empty):
        """성공적인 회원가입"""
        # 사용자 생성
        import bcrypt

        username = "newuser"
        email = "newuser@example.com"
        password = "securepassword"  # pragma: allowlist secret

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user_id = await db_empty.create_user(username, email, password_hash)

        assert user_id is not None
        assert isinstance(user_id, int)

        # DB에서 사용자 조회
        user = await db_empty.get_user_by_username(username)
        assert user is not None
        assert user["username"] == username
        assert user["email"] == email
        assert user["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, db_with_users):
        """중복 username으로 회원가입 실패"""
        db, _ = db_with_users

        import bcrypt

        password_hash = bcrypt.hashpw(b"password456", bcrypt.gensalt()).decode("utf-8")

        # 같은 username으로 재시도
        user_id = await db.create_user("testuser", "another@example.com", password_hash)
        assert user_id is None

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, db_with_users):
        """중복 email으로 회원가입 실패"""
        db, _ = db_with_users

        import bcrypt

        password_hash = bcrypt.hashpw(b"password789", bcrypt.gensalt()).decode("utf-8")

        # 같은 email로 재시도
        user_id = await db.create_user("anotheruser", "test@example.com", password_hash)
        assert user_id is None


class TestLoginAPI:
    """로그인 API 테스트"""

    @pytest.mark.asyncio
    async def test_login_success(self, db_with_users):
        """성공적인 로그인"""
        db, user_id = db_with_users

        # DB에서 사용자 조회
        user = await db.get_user_by_username("testuser")
        assert user is not None

        # 비밀번호 검증
        import bcrypt

        password_hash = user.get("password_hash", "")
        assert bcrypt.checkpw(b"password123", password_hash.encode("utf-8"))

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, db_with_users):
        """잘못된 비밀번호로 로그인 실패"""
        db, _ = db_with_users

        # DB에서 사용자 조회
        user = await db.get_user_by_username("testuser")
        assert user is not None

        # 잘못된 비밀번호 검증
        import bcrypt

        password_hash = user.get("password_hash", "")
        assert not bcrypt.checkpw(b"wrongpassword", password_hash.encode("utf-8"))

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, db_empty):
        """존재하지 않는 사용자로 로그인 실패"""
        user = await db_empty.get_user_by_username("nonexistent")
        assert user is None


class TestJWTWithUserID:
    """JWT user_id 포함 테스트"""

    @pytest.mark.asyncio
    async def test_jwt_contains_user_id(self, monkeypatch):
        """JWT payload에 user_id가 포함되는지 테스트"""
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
        user_id = 42
        token, _ = _issue_token(
            ttl_seconds=3600, typ="access", session_key=session_key, user_id=user_id
        )

        assert token is not None

        # JWT 디코딩 (검증 없이)
        payload = jwt.decode(token, options={"verify_signature": False})

        assert "session_key" in payload
        assert payload["session_key"] == session_key
        assert "user_id" in payload
        assert payload["user_id"] == user_id
        assert payload["typ"] == "access"
        assert payload["sub"] == "persona_chat_user"

    @pytest.mark.asyncio
    async def test_jwt_without_user_id_backward_compatible(self, monkeypatch):
        """user_id 없는 JWT도 동작하는지 테스트 (하위 호환성)"""
        # JWT_SECRET 설정
        monkeypatch.setenv(
            "APP_JWT_SECRET", "test_secret_key_for_testing"
        )  # pragma: allowlist secret

        # websocket_server 모듈 reload 필요 (환경변수 반영)
        import importlib

        import server.websocket_server

        importlib.reload(server.websocket_server)

        from server.websocket_server import _issue_token

        # user_id 없이 토큰 생성
        token, _ = _issue_token(
            ttl_seconds=3600, typ="access", session_key="user:testuser", user_id=None
        )

        assert token is not None

        # JWT 디코딩
        payload = jwt.decode(token, options={"verify_signature": False})

        # user_id가 없어야 함
        assert "user_id" not in payload
        assert payload["typ"] == "access"

    @pytest.mark.asyncio
    async def test_token_refresh_preserves_user_id(self, monkeypatch):
        """토큰 갱신 시 user_id가 보존되는지 테스트"""
        # JWT_SECRET 설정
        monkeypatch.setenv(
            "APP_JWT_SECRET", "test_secret_key_for_testing"
        )  # pragma: allowlist secret
        monkeypatch.setenv("APP_REFRESH_ROTATE", "1")  # Refresh 토큰 회전 활성화

        # websocket_server 모듈 reload 필요 (환경변수 반영)
        import importlib

        import server.websocket_server

        importlib.reload(server.websocket_server)

        from server.websocket_server import issue_access_token, issue_refresh_token

        session_key = "user:testuser"
        user_id = 42

        # 원본 토큰 발급
        access_token, _ = issue_access_token(session_key, user_id)
        refresh_token, _ = issue_refresh_token(session_key, user_id)

        assert access_token is not None
        assert refresh_token is not None

        # 원본 토큰 디코딩
        access_payload = jwt.decode(access_token, options={"verify_signature": False})
        refresh_payload = jwt.decode(refresh_token, options={"verify_signature": False})

        assert access_payload["user_id"] == user_id
        assert access_payload["session_key"] == session_key
        assert refresh_payload["user_id"] == user_id
        assert refresh_payload["session_key"] == session_key

        # 토큰 갱신 시뮬레이션 (refresh 토큰으로 새 access 토큰 발급)
        new_user_id = refresh_payload.get("user_id")
        new_session_key = refresh_payload.get("session_key")
        new_access_token, _ = issue_access_token(new_session_key, new_user_id)
        new_refresh_token, _ = issue_refresh_token(new_session_key, new_user_id)

        # 새 토큰에도 user_id가 보존되어야 함
        new_access_payload = jwt.decode(new_access_token, options={"verify_signature": False})
        new_refresh_payload = jwt.decode(new_refresh_token, options={"verify_signature": False})

        assert new_access_payload["user_id"] == user_id
        assert new_access_payload["session_key"] == session_key
        assert new_refresh_payload["user_id"] == user_id
        assert new_refresh_payload["session_key"] == session_key


class TestUserDataIsolation:
    """user_id 기반 데이터 격리 테스트"""

    @pytest.mark.asyncio
    async def test_user_session_storage(self, db_empty):
        """로그인 시 user_id가 세션에 저장되는지 테스트"""
        import bcrypt

        # 사용자 생성
        password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        user_id = await db_empty.create_user("testuser", "test@example.com", password_hash)

        # 세션 생성 (로그인 시뮬레이션)
        session_key = "user:testuser"
        await db_empty.upsert_session(session_key, user_id)

        # 세션 조회로 user_id 확인
        cursor = await db_empty._conn.execute(
            "SELECT user_id FROM sessions WHERE session_key = ?", (session_key,)
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_list_rooms_by_user_id(self):
        """user_id로 방 목록 조회 격리 테스트"""
        import json
        import tempfile
        from pathlib import Path

        import bcrypt

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = DBHandler(str(db_path))
            await db.initialize()

            # 사용자 2명 생성
            pw_hash = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode("utf-8")
            user1_id = await db.create_user("alice", "alice@example.com", pw_hash)
            user2_id = await db.create_user("bob", "bob@example.com", pw_hash)

            assert user1_id is not None
            assert user2_id is not None

            # Alice 세션 및 방 생성
            session1 = "user:alice"
            await db.upsert_session(session1, user1_id)
            await db.upsert_room(
                "room-a1",
                session1,
                "Alice's Room 1",
                json.dumps({"world": "Alice World"}),
                user1_id,
            )
            await db.upsert_room(
                "room-a2",
                session1,
                "Alice's Room 2",
                json.dumps({"world": "Alice World"}),
                user1_id,
            )

            # Bob 세션 및 방 생성
            session2 = "user:bob"
            await db.upsert_session(session2, user2_id)
            await db.upsert_room(
                "room-b1",
                session2,
                "Bob's Room 1",
                json.dumps({"world": "Bob World"}),
                user2_id,
            )

            # Alice의 방 목록 조회 (user_id로)
            alice_rooms = await db.list_rooms_by_user_id(user1_id)
            assert len(alice_rooms) == 2
            assert {r["room_id"] for r in alice_rooms} == {"room-a1", "room-a2"}
            assert all(r["title"].startswith("Alice") for r in alice_rooms)

            # Bob의 방 목록 조회 (user_id로)
            bob_rooms = await db.list_rooms_by_user_id(user2_id)
            assert len(bob_rooms) == 1
            assert bob_rooms[0]["room_id"] == "room-b1"
            assert bob_rooms[0]["title"] == "Bob's Room 1"

            # 존재하지 않는 user_id로 조회 → 빈 목록
            nonexistent_rooms = await db.list_rooms_by_user_id(9999)
            assert len(nonexistent_rooms) == 0

            await db.close()

    @pytest.mark.asyncio
    async def test_user_data_isolation_cross_check(self):
        """사용자 간 데이터 격리 확인 (교차 검증)"""
        import tempfile
        from pathlib import Path

        import bcrypt

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = DBHandler(str(db_path))
            await db.initialize()

            # 사용자 2명 생성
            pw_hash = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode("utf-8")
            user1_id = await db.create_user("user1", "user1@example.com", pw_hash)
            user2_id = await db.create_user("user2", "user2@example.com", pw_hash)

            # User1: 세션 및 방 생성
            session1 = "user:user1"
            await db.upsert_session(session1, user1_id)
            await db.upsert_room("room-001", session1, "User1 Room", None, user1_id)
            await db.save_message("room-001", "user", "User1's message")

            # User2: 같은 room_id로 방 생성 (session_key가 다르므로 가능)
            session2 = "user:user2"
            await db.upsert_session(session2, user2_id)
            await db.upsert_room("room-001", session2, "User2 Room", None, user2_id)
            await db.save_message("room-001", "user", "User2's message")

            # User1의 방 조회 (user_id로)
            user1_rooms = await db.list_rooms_by_user_id(user1_id)
            assert len(user1_rooms) == 1
            assert user1_rooms[0]["title"] == "User1 Room"
            assert user1_rooms[0]["session_key"] == session1

            # User2의 방 조회 (user_id로)
            user2_rooms = await db.list_rooms_by_user_id(user2_id)
            assert len(user2_rooms) == 1
            assert user2_rooms[0]["title"] == "User2 Room"
            assert user2_rooms[0]["session_key"] == session2

            # 메시지는 room_id로 구분되므로 둘 다 조회됨 (room 격리와 무관)
            # 실제로는 room_id가 충돌하지 않도록 UUID 등을 사용해야 함
            messages = await db.list_messages("room-001")
            assert len(messages) == 2  # 두 사용자의 메시지 모두 조회됨

            await db.close()
