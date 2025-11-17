import json
import logging

import pytest

from server.core import session_manager as sm
from server.core.app_context import AppContext
from server.handlers.context_handler import ContextHandler
from server.ws.actions import context as ctx_actions


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
async def test_set_context_with_room_id_and_user_id(tmp_path, monkeypatch, caplog):
    """Test set_context with room_id and user_id to cover lines 60, 62, 64, 66, 68"""
    ctx = make_ctx(tmp_path)
    ch = ContextHandler()
    ctx.context_handler = ch
    ws = FakeWS()

    # Mock DB that tracks calls
    calls = []

    class DB:
        async def upsert_room(self, room_id, user_id, title, context_json):
            calls.append(("upsert", room_id, user_id, title, context_json))
            return True

        async def get_room(self, *a, **k):
            return None

    ctx.db_handler = DB()

    # First test with valid user_id (covers lines 60, 62, 68)
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: 42)

    await ctx_actions.set_context(ctx, ws, {"room_id": "r1", "world": "W"})

    # Verify DB was called
    assert len(calls) == 1
    assert calls[0][0] == "upsert"
    assert calls[0][1] == "r1"
    assert calls[0][2] == 42
    assert "world" in calls[0][4]  # context_json contains world

    # Now test with missing user_id (covers lines 60, 62, 64, 66)
    calls.clear()
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: None)

    with caplog.at_level(logging.WARNING):
        await ctx_actions.set_context(ctx, ws, {"room_id": "r2", "world": "W2"})

    # Verify DB was NOT called and warning was logged
    assert len(calls) == 0
    assert any(
        "No user_id found in token, skipping DB save" in rec.message for rec in caplog.records
    )


@pytest.mark.asyncio
async def test_set_context_session_reset_clears_sessions(tmp_path, monkeypatch, caplog):
    """Test session reset path to cover lines 112-113"""
    ctx = make_ctx(tmp_path)
    ch = ContextHandler()
    ctx.context_handler = ch
    ws = FakeWS()

    # Track clear_client_sessions calls
    cleared = []

    def fake_clear(c, w):
        cleared.append((c, w))

    monkeypatch.setattr(sm, "clear_client_sessions", fake_clear)
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: 42)

    # Set initial context
    ch.set_adult_level("general")

    # Change a key that triggers session reset (adult_level)
    await ctx_actions.set_context(ctx, ws, {"room_id": "r1", "adult_level": "explicit"})

    # Verify sessions were cleared
    assert len(cleared) == 1
    assert cleared[0][0] is ctx
    assert cleared[0][1] is ws

    # Check out response
    out = json.loads(ws.sent[-1])
    assert out["action"] == "set_context"
    assert out["data"]["success"] is True
    assert out["data"]["context"]["adult_level"] == "explicit"
