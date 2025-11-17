import json

import pytest

from server.core import session_manager as sm
from server.core.app_context import AppContext
from server.ws.actions import chat as chat_actions


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

    # minimal handlers used by chat
    class CH:
        def get_context(self):
            return {}

        def build_system_prompt(self, history_text):
            return "sys"

    ctx.context_handler = CH()
    ctx.token_usage_handler = type(
        "T", (), {"add_usage": lambda *a, **k: None, "get_formatted_summary": lambda *a, **k: {}}
    )()
    # handlers
    ctx.claude_handler = None
    ctx.droid_handler = None
    ctx.gemini_handler = None
    ctx.db_handler = None
    # session/storage
    ctx.sessions = {}
    ctx.websocket_to_session = {}
    return ctx


@pytest.mark.asyncio
async def test_chat_requires_auth(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: None)

    await chat_actions.chat(ctx, ws, {"prompt": "hi"})
    msg = json.loads(ws.sent[-1])
    assert msg["action"] == "chat_complete"
    assert msg["data"]["success"] is False


@pytest.mark.asyncio
async def test_chat_adult_consent_required(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()

    # context demands enhanced level
    class CH2:
        def get_context(self):
            return {"adult_level": "enhanced"}

        def build_system_prompt(self, history_text):
            return "sys"

    ctx.context_handler = CH2()
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: 4)

    # do not set adult_consent in session -> consent_required
    await chat_actions.chat(ctx, ws, {"prompt": "x"})
    msg = json.loads(ws.sent[-1])
    assert msg["action"] == "consent_required"
    assert msg["data"]["required"] is True


@pytest.mark.asyncio
async def test_chat_success_and_token_usage(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()

    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: 3)

    async def fake_send_message(prompt, system_prompt, callback, session_id, model=None):
        # call callback once
        await callback({"partial": True})
        return {
            "success": True,
            "message": "response text",
            "token_info": {"input_tokens": 1, "output_tokens": 2},
            "session_id": "sess-1",
        }

    class FakeHandler:
        send_message = staticmethod(fake_send_message)

    ctx.claude_handler = FakeHandler()

    await chat_actions.chat(ctx, ws, {"prompt": "hello", "provider": "claude"})
    # last message should be chat_complete
    msg = json.loads(ws.sent[-1])
    assert msg["action"] == "chat_complete"
    assert msg["data"]["provider_used"] == "claude"
    assert msg["data"]["success"] is True
