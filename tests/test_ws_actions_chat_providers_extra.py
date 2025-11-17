import json

import pytest

from server.core import session_manager as sm
from server.core.app_context import AppContext
from server.ws.actions import chat as chat_actions


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

    # context handler returns build_system_prompt echoing history_text
    class CH:
        def get_context(self):
            return {}

        def build_system_prompt(self, history_text):
            return f"SP:{history_text}"

    ctx.context_handler = CH()
    ctx.token_usage_handler = type(
        "T", (), {"add_usage": lambda *a, **k: None, "get_formatted_summary": lambda *a, **k: {}}
    )()
    ctx.claude_handler = None
    ctx.droid_handler = None
    ctx.gemini_handler = None
    ctx.db_handler = None
    ctx.sessions = {}
    ctx.websocket_to_session = {}
    return ctx


@pytest.mark.asyncio
async def test_droid_skips_history_when_provider_session_present(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: 101)

    # create session and room and set provider session id
    _, sess = sm.get_or_create_session(ctx, ws, 101)
    _, room = sm.get_room(ctx, sess, None)
    room.setdefault("provider_sessions", {})["droid"] = "psid-1"

    captured = []

    async def fake_send_message(prompt, system_prompt, callback, session_id, model=None):
        captured.append(system_prompt)
        await callback({"partial": True})
        return {"success": True, "message": "r", "token_info": None, "session_id": None}

    class DH:
        send_message = staticmethod(fake_send_message)

    ctx.droid_handler = DH()

    await chat_actions.chat(ctx, ws, {"prompt": "p", "provider": "droid"})
    # since provider_session existed, system_prompt should be SP:
    assert captured and captured[0] == "SP:"
    last = json.loads(ws.sent[-1])
    assert last["action"] == "chat_complete"


@pytest.mark.asyncio
async def test_gemini_receives_history_text_when_no_provider_session(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: 202)

    # create session and room and add some history
    _, sess = sm.get_or_create_session(ctx, ws, 202)
    _, room = sm.get_room(ctx, sess, None)
    room["history"].add_user_message("hello-world")

    captured = []

    async def fake_send_message(prompt, system_prompt, callback, session_id, model=None):
        captured.append(system_prompt)
        await callback({"partial": True})
        return {"success": True, "message": "r2", "token_info": None, "session_id": "s2"}

    class GH:
        send_message = staticmethod(fake_send_message)

    ctx.gemini_handler = GH()

    await chat_actions.chat(ctx, ws, {"prompt": "p", "provider": "gemini"})
    # build_system_prompt should have received history with 'hello-world'
    assert captured and "hello-world" in captured[0]
    last = json.loads(ws.sent[-1])
    assert last["action"] == "chat_complete"
    assert last["data"]["provider_used"] == "gemini"
