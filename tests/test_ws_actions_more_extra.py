import json

import pytest

from server.core import session_manager as sm
from server.core.app_context import AppContext
from server.handlers.context_handler import ContextHandler
from server.handlers.token_usage_handler import TokenUsageHandler
from server.handlers.workspace_handler import WorkspaceHandler
from server.ws.actions import context as ctx_actions
from server.ws.actions import history as history_actions
from server.ws.actions import presets as presets_actions
from server.ws.actions import session as session_actions
from server.ws.actions import stories as stories_actions
from server.ws.actions import token_usage as token_usage_actions


class FakeWS:
    def __init__(self):
        self.sent = []
        self.remote_address = ("127.0.0.1", 1234)

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
    ctx.context_handler = ContextHandler()
    ctx.workspace_handler = WorkspaceHandler(str(tmp_path / "persona_data"))
    ctx.token_usage_handler = TokenUsageHandler()
    ctx.token_usage_handler.session_usage = {}
    # sessions mapping used by session_manager
    ctx.sessions = {}
    ctx.websocket_to_session = {}
    return ctx


@pytest.mark.asyncio
async def test_context_set_get_without_db(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()

    # set_context without room_id
    await ctx_actions.set_context(ctx, ws, {"world": "W", "situation": "S"})
    msg = json.loads(ws.sent[-1])
    assert msg["action"] == "set_context"
    assert msg["data"]["success"] is True
    assert msg["data"]["context"]["world"] == "W"

    # get_context returns current context
    await ctx_actions.get_context(ctx, ws, {})
    gm = json.loads(ws.sent[-1])
    assert gm["action"] == "get_context"
    assert gm["data"]["success"] is True

    # set_context with room_id but no db_handler -> should not crash
    await ctx_actions.set_context(ctx, ws, {"room_id": "r1", "world": "X"})
    assert json.loads(ws.sent[-1])["data"]["success"] is True


@pytest.mark.asyncio
async def test_context_get_with_db(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()

    # fake db_handler.get_room returns stored context JSON
    async def fake_get_room(room_id, user_id):
        return {"room_id": room_id, "title": "T", "context": json.dumps({"world": "DBW"})}

    class DB:
        get_room = staticmethod(fake_get_room)

    ctx.db_handler = DB()
    # make auth return user_id
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: 7)

    await ctx_actions.get_context(ctx, ws, {"room_id": "r1", "token": "x"})
    msg = json.loads(ws.sent[-1])
    assert msg["action"] == "get_context"
    assert msg["data"]["context"]["world"] == "DBW"


@pytest.mark.asyncio
async def test_history_actions_and_snapshot(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()

    # auth
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: 11)

    # get_narrative when empty
    await history_actions.get_narrative(ctx, ws, {})
    m = json.loads(ws.sent[-1])
    assert m["action"] == "get_narrative"
    assert m["data"]["success"] is True

    # add messages
    _, sess = sm.get_or_create_session(ctx, ws, 11)
    _, room = sm.get_room(ctx, sess, None)
    room["history"].add_user_message("hello")
    room["history"].add_assistant_message("hi")

    await history_actions.get_narrative(ctx, ws, {})
    m2 = json.loads(ws.sent[-1])
    assert "hello" in m2["data"]["markdown"]

    # get_history_settings
    await history_actions.get_history_settings(ctx, ws, {})
    hs = json.loads(ws.sent[-1])
    assert hs["action"] == "get_history_settings"
    assert hs["data"]["max_turns"] == room["history"].max_turns

    # set_history_limit -> None
    await history_actions.set_history_limit(ctx, ws, {"max_turns": None})
    sh = json.loads(ws.sent[-1])
    assert sh["data"]["success"] is True

    # snapshot
    await history_actions.get_history_snapshot(ctx, ws, {})
    snap = json.loads(ws.sent[-1])
    assert snap["data"]["success"] is True
    assert isinstance(snap["data"]["history"], list)

    # clear_history
    await history_actions.clear_history(ctx, ws, {})
    cl = json.loads(ws.sent[-1])
    assert cl["data"]["success"] is True

    # reset_sessions (should succeed)
    await history_actions.reset_sessions(ctx, ws, {})
    rs = json.loads(ws.sent[-1])
    assert rs["data"]["success"] is True


@pytest.mark.asyncio
async def test_session_actions(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: 22)

    await session_actions.get_session_settings(ctx, ws, {})
    msg = json.loads(ws.sent[-1])
    assert msg["data"]["success"] is True

    await session_actions.set_session_retention(ctx, ws, {})
    msg2 = json.loads(ws.sent[-1])
    assert msg2["data"]["success"] is True


@pytest.mark.asyncio
async def test_presets_and_stories_and_token_usage(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()

    # presets: list/save/load/delete
    await presets_actions.list_presets(ctx, ws, {})
    p = json.loads(ws.sent[-1])
    assert p["action"] == "list_presets"

    await presets_actions.save_preset(ctx, ws, {"filename": "p1", "preset": {"a": 1}})
    s = json.loads(ws.sent[-1])
    assert s["action"] == "save_preset"

    await presets_actions.load_preset(ctx, ws, {"filename": "p1"})
    load_msg = json.loads(ws.sent[-1])
    assert load_msg["action"] == "load_preset"

    await presets_actions.delete_preset(ctx, ws, {"filename": "p1"})
    d = json.loads(ws.sent[-1])
    assert d["action"] == "delete_preset"

    # stories (disabled)
    await stories_actions.list_stories(ctx, ws, {})
    ls = json.loads(ws.sent[-1])
    assert ls["data"]["files"] == []

    await stories_actions.save_story(ctx, ws, {})
    ss = json.loads(ws.sent[-1])
    assert ss["data"]["success"] is False

    # token_usage: need auth
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: None)
    await token_usage_actions.get_token_usage(ctx, ws, {})
    tno = json.loads(ws.sent[-1])
    assert tno["data"]["success"] is False

    # with auth and some usage
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: 9)
    # add usage
    ctx.token_usage_handler.add_usage(
        "9", "default", "claude", {"input_tokens": 1, "output_tokens": 2}
    )
    await token_usage_actions.get_token_usage(ctx, ws, {"room_id": "default"})
    t = json.loads(ws.sent[-1])
    assert t["data"]["success"] is True
    assert "claude" in t["data"]["token_usage"]["providers"]
