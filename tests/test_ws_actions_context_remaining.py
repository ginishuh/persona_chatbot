import json

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
async def test_set_get_context_handler_missing(tmp_path):
    ctx = make_ctx(tmp_path)
    ctx.context_handler = None
    ws = FakeWS()

    # set_context should report missing handler and not crash
    await ctx_actions.set_context(ctx, ws, {"world": "W"})
    msg = json.loads(ws.sent[-1])
    assert msg["action"] == "set_context"
    assert msg["data"]["success"] is False
    assert "context handler missing" in msg["data"]["error"]

    # get_context should report missing handler as well
    await ctx_actions.get_context(ctx, ws, {})
    gm = json.loads(ws.sent[-1])
    assert gm["action"] == "get_context"
    assert gm["data"]["success"] is False
    assert "context handler missing" in gm["data"]["error"]


@pytest.mark.asyncio
async def test_set_and_get_context_db_user_missing_skips_db(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ch = ContextHandler()
    ctx.context_handler = ch
    ws = FakeWS()

    # Provide a DB handler that would raise if called (to ensure it's skipped)
    class DB:
        async def upsert_room(self, *a, **k):
            raise AssertionError("upsert_room should not be called when user_id missing")

        async def get_room(self, *a, **k):
            raise AssertionError("get_room should not be called when user_id missing")

    ctx.db_handler = DB()

    # Simulate missing user_id from token
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: None)

    # Call set_context with room_id; DB upsert should be skipped
    await ctx_actions.set_context(ctx, ws, {"room_id": "r1", "world": "X"})
    out = json.loads(ws.sent[-1])
    assert out["action"] == "set_context"
    assert out["data"]["success"] is True
    assert out["data"]["context"]["world"] == "X"

    # Now call get_context with room_id; DB get should be skipped and context returned
    await ctx_actions.get_context(ctx, ws, {"room_id": "r1"})
    gm = json.loads(ws.sent[-1])
    assert gm["action"] == "get_context"
    assert gm["data"]["success"] is True
    assert gm["data"]["context"]["world"] == "X"
