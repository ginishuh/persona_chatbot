import json
from pathlib import Path

import jwt
import pytest

import server.core.session_manager as sm
import server.websocket_server as ws_srv
from server.core.app_context import AppContext


class FakeWebSocket:
    def __init__(self):
        self.sent = []
        self.remote_address = ("127.0.0.1", 12345)

    async def send(self, message):
        self.sent.append(message)


def make_app_ctx(secret="testsecret"):  # pragma: allowlist secret
    return AppContext(
        project_root=Path("."),
        bind_host="127.0.0.1",
        login_required=False,
        jwt_secret=secret,
        jwt_algorithm="HS256",
        access_ttl_seconds=60,
        refresh_ttl_seconds=120,
        login_username="",
        login_rate_limit_max_attempts=5,
        login_rate_limit_window_seconds=900,
        token_expired_grace_seconds=60,
    )


def test_issue_token_no_secret():
    # Ensure no secret yields no token
    prev = ws_srv.JWT_SECRET
    ws_srv.JWT_SECRET = ""
    token, exp = ws_srv._issue_token(10, "access")
    assert token is None and exp is None
    ws_srv.JWT_SECRET = prev


def test_issue_and_verify_tokens():
    # Setup secret in module and APP_CTX
    ws_srv.JWT_SECRET = "unit-test-secret"  # pragma: allowlist secret
    ws_srv.JWT_ALGORITHM = "HS256"
    ctx = make_app_ctx(secret="unit-test-secret")
    ws_srv.APP_CTX = ctx

    access, _ = ws_srv.issue_access_token(user_id=7)
    assert access is not None

    payload, error = ws_srv.verify_token(access, expected_type="access")
    assert error is None
    assert payload.get("user_id") == 7


@pytest.mark.asyncio
async def test_handle_token_refresh_action_success():
    ws_srv.JWT_SECRET = "unit-test-secret"  # pragma: allowlist secret
    ws_srv.JWT_ALGORITHM = "HS256"
    ctx = make_app_ctx(secret="unit-test-secret")
    ws_srv.APP_CTX = ctx

    # create a refresh token
    refresh_token, _ = ws_srv.issue_refresh_token(user_id=42)

    ws = FakeWebSocket()
    await ws_srv.handle_token_refresh_action(ws, {"refresh_token": refresh_token})

    assert ws.sent
    msg = json.loads(ws.sent[-1])
    assert msg["action"] == "token_refresh"
    assert msg["data"]["success"] is True
    assert msg["data"].get("token")
    assert msg["data"].get("refresh_token")


@pytest.mark.asyncio
async def test_handle_token_refresh_action_invalid_token():
    ws_srv.JWT_SECRET = "unit-test-secret"  # pragma: allowlist secret
    ws_srv.JWT_ALGORITHM = "HS256"
    ctx = make_app_ctx(secret="unit-test-secret")
    ws_srv.APP_CTX = ctx

    ws = FakeWebSocket()
    await ws_srv.handle_token_refresh_action(ws, {"refresh_token": "not-a-token"})
    msg = json.loads(ws.sent[-1])
    assert msg["action"] == "token_refresh"
    assert msg["data"]["success"] is False


@pytest.mark.asyncio
async def test_handle_message_branches():
    ws_srv.JWT_SECRET = "unit-test-secret"  # pragma: allowlist secret
    ws_srv.JWT_ALGORITHM = "HS256"
    ws_srv.APP_CTX = make_app_ctx(secret="unit-test-secret")

    ws = FakeWebSocket()
    # login action
    await ws_srv.handle_message(ws, json.dumps({"action": "login"}))
    msg = json.loads(ws.sent[-1])
    assert msg["action"] == "login"
    assert msg["data"]["code"] == "deprecated"

    # unknown action
    await ws_srv.handle_message(ws, json.dumps({"action": "i_dont_exist"}))
    msg = json.loads(ws.sent[-1])
    assert msg["action"] == "error"
    assert "Unknown action" in msg["data"]["error"]

    # invalid json
    await ws_srv.handle_message(ws, "notjson")
    msg = json.loads(ws.sent[-1])
    assert msg["action"] == "error"
    assert msg["data"]["error"] == "Invalid JSON"


def test_get_user_id_from_token_and_sessions():
    secret = "unit-test-secret"  # pragma: allowlist secret
    ctx = make_app_ctx(secret=secret)

    # create a token payload with user_id
    now = int(__import__("time").time())
    payload = {
        "sub": "persona_chat_user",
        "iat": now,
        "exp": now + 60,
        "typ": "access",
        "user_id": 123,
    }
    token = jwt.encode(payload, secret, algorithm="HS256")

    user_id = sm.get_user_id_from_token(ctx, {"token": token})
    assert user_id == 123


def test_get_or_create_and_room_management():
    ctx = make_app_ctx()
    websocket = object()
    uid, session = sm.get_or_create_session(ctx, websocket, 55)
    assert uid == 55
    assert 55 in ctx.sessions

    rid, room = sm.get_room(ctx, session, None)
    assert rid == "default"
    assert "history" in room

    # remove mapping
    sm.remove_client_sessions(ctx, websocket)
    assert websocket not in ctx.websocket_to_session
