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
