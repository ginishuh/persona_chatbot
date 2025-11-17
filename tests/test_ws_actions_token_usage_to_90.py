import json

import pytest

from server.core import session_manager as sm
from server.core.app_context import AppContext
from server.ws.actions import token_usage


class FakeWS:
    def __init__(self):
        self.sent = []

    async def send(self, msg):
        self.sent.append(msg)


def make_ctx(tmp_path):
    ctx = AppContext(
        project_root=tmp_path,
        bind_host="127.0.0.1",
        login_required=False,
        jwt_secret="s",
        jwt_algorithm="HS256",
        access_ttl_seconds=60,
        refresh_ttl_seconds=120,
        login_username="",
        login_rate_limit_max_attempts=5,
        login_rate_limit_window_seconds=900,
        token_expired_grace_seconds=60,
    )
    return ctx


@pytest.mark.asyncio
async def test_get_token_usage_no_user_id(tmp_path, monkeypatch):
    """Test get_token_usage with no user_id to cover line 32"""
    ctx = make_ctx(tmp_path)
    ws = FakeWS()

    # Mock get_user_id_from_token to return None
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: None)

    await token_usage.get_token_usage(ctx, ws, {})

    # Check error response
    out = json.loads(ws.sent[-1])
    assert out["action"] == "get_token_usage"
    assert out["data"]["success"] is False
    assert out["data"]["error"] == "인증 필요"


@pytest.mark.asyncio
async def test_get_token_usage_exception_handling(tmp_path, monkeypatch):
    """Test get_token_usage exception handling to cover line 33"""
    ctx = make_ctx(tmp_path)
    ws = FakeWS()

    # Mock get_user_id_from_token to raise an exception
    def raise_exception(c, d):
        raise RuntimeError("Test exception")

    monkeypatch.setattr(sm, "get_user_id_from_token", raise_exception)

    await token_usage.get_token_usage(ctx, ws, {})

    # Check error response
    out = json.loads(ws.sent[-1])
    assert out["action"] == "get_token_usage"
    assert out["data"]["success"] is False
    assert "Test exception" in out["data"]["error"]
