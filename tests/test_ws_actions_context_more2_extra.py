import json

import pytest

from server.core import session_manager as sm
from server.core.app_context import AppContext
from server.ws.actions import context as ctx_actions


class FakeWS:
    def __init__(self):
        self.sent = []

    async def send(self, msg):
        self.sent.append(msg)


def make_basic_ctx(tmp_path):
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

    # simple context handler
    class CH:
        def __init__(self):
            self._ctx = {}

        def get_context(self):
            return dict(self._ctx)

        def set_world(self, v):
            self._ctx["world"] = v

        def set_situation(self, v):
            self._ctx["situation"] = v

        def set_user_character(self, v):
            self._ctx["user_character"] = v

        def set_narrator(self, enabled, mode, description, user_is_narrator):
            self._ctx["narrator_enabled"] = enabled
            self._ctx["narrator_mode"] = mode
            self._ctx["narrator_description"] = description
            self._ctx["user_is_narrator"] = user_is_narrator

        def set_adult_level(self, v):
            self._ctx["adult_level"] = v

        def set_narrative_separation(self, v):
            self._ctx["narrative_separation"] = v

        def set_ai_provider(self, v):
            self._ctx["ai_provider"] = v

        def set_characters(self, v):
            self._ctx["characters"] = v

        def set_output_level(self, v):
            self._ctx["output_level"] = v

        def set_pace(self, v):
            self._ctx["pace"] = v

        def set_narrator_drive(self, v):
            self._ctx["narrator_drive"] = v

        def set_choice_policy(self, v):
            self._ctx["choice_policy"] = v

        def set_choice_count(self, v):
            self._ctx["choice_count"] = v

        def load_from_dict(self, d):
            self._ctx.update(d)

    ctx.context_handler = CH()
    ctx.sessions = {}
    ctx.websocket_to_session = {}
    return ctx


@pytest.mark.asyncio
async def test_set_context_error_when_no_handler(tmp_path):
    ctx = make_basic_ctx(tmp_path)
    ws = FakeWS()
    ctx.context_handler = None

    await ctx_actions.set_context(ctx, ws, {"world": "X"})
    out = json.loads(ws.sent[-1])
    assert out["action"] == "set_context"
    assert out["data"]["success"] is False
    assert "context handler missing" in out["data"]["error"]


@pytest.mark.asyncio
async def test_get_context_error_when_no_handler(tmp_path):
    ctx = make_basic_ctx(tmp_path)
    ws = FakeWS()
    ctx.context_handler = None

    await ctx_actions.get_context(ctx, ws, {})
    out = json.loads(ws.sent[-1])
    assert out["action"] == "get_context"
    assert out["data"]["success"] is False


@pytest.mark.asyncio
async def test_set_context_with_db_but_no_user_skips_db(tmp_path, monkeypatch):
    ctx = make_basic_ctx(tmp_path)
    ws = FakeWS()

    called = {"upsert": False}

    class DB:
        async def get_room(self, room_id, user_id):
            return None

        async def upsert_room(self, room_id, user_id, title, context_json):
            called["upsert"] = True

    ctx.db_handler = DB()
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: None)

    await ctx_actions.set_context(ctx, ws, {"room_id": "r1", "world": "W"})
    out = json.loads(ws.sent[-1])
    assert out["data"]["success"] is True
    assert called["upsert"] is False


@pytest.mark.asyncio
async def test_get_context_with_db_but_no_user_skips_load(tmp_path, monkeypatch):
    ctx = make_basic_ctx(tmp_path)
    ws = FakeWS()

    class DB:
        async def get_room(self, room_id, user_id):
            return {"room_id": room_id, "title": "T", "context": json.dumps({"a": 1})}

    ctx.db_handler = DB()
    # simulate missing user_id
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: None)

    await ctx_actions.get_context(ctx, ws, {"room_id": "r1"})
    out = json.loads(ws.sent[-1])
    # get_context should still succeed but not load from DB when no user_id
    assert out["action"] == "get_context"
    assert out["data"]["success"] is True
