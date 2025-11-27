import json

import pytest

from server.core import session_manager as sm
from server.core.app_context import AppContext
from server.handlers.context_handler import ContextHandler
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

    class CH:
        def __init__(self):
            self._ctx = {}

        def get_context(self):
            return self._ctx

        def update_context(self, updates):
            self._ctx.update(updates)

        def build_system_prompt(self, history_text):
            return "sys"

    ctx.context_handler = CH()
    ctx.token_usage_handler = type(
        "T", (), {"add_usage": lambda *a, **k: None, "get_formatted_summary": lambda *a, **k: {}}
    )()
    ctx.claude_handler = None
    ctx.droid_handler = None
    ctx.gemini_handler = None
    ctx.sessions = {}
    ctx.websocket_to_session = {}
    return ctx


@pytest.mark.asyncio
async def test_db_exceptions_do_not_crash_and_token_usage_added(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: 50)

    # db handler methods that raise
    class DB:
        async def get_room(self, rid, user_id):
            return None

        async def upsert_room(self, rid, user_id, title, context):
            raise RuntimeError("db upsert fail")

        async def save_message(self, rid, role, content, user_id):
            raise RuntimeError("db save fail")

        async def save_token_usage(self, user_id, room_id, provider, token_info):
            raise RuntimeError("db token fail")

    ctx.db_handler = DB()

    async def fake_send_message(prompt, system_prompt, callback, session_id, model=None):
        await callback({})
        return {
            "success": True,
            "message": "resp",
            "token_info": {"input_tokens": 1},
            "session_id": None,
        }

    class FH:
        send_message = staticmethod(fake_send_message)

    ctx.claude_handler = FH()

    await chat_actions.chat(ctx, ws, {"prompt": "p", "provider": "claude"})
    last = json.loads(ws.sent[-1])
    assert last["action"] == "chat_complete"
    assert last["data"]["success"] is True


@pytest.mark.asyncio
async def test_provider_session_update_and_clear(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: 60)

    # 세션유지 ON으로 설정
    ctx.context_handler.update_context({"session_retention": True})

    # create session and room
    _, sess = sm.get_or_create_session(ctx, ws, 60)
    _, room = sm.get_room(ctx, sess, None)

    # first response returns session_id -> should set provider_sessions
    async def send_with_session(prompt, system_prompt, callback, session_id, model=None):
        await callback({})
        return {"success": True, "message": "m1", "token_info": None, "session_id": "S1"}

    class H1:
        send_message = staticmethod(send_with_session)

    ctx.claude_handler = H1()
    await chat_actions.chat(ctx, ws, {"prompt": "x", "provider": "claude"})
    assert room.setdefault("provider_sessions", {}).get("claude") == "S1"

    # 세션유지 OFF로 변경 -> 세션 정보 삭제됨
    ctx.context_handler.update_context({"session_retention": False})

    async def send_no_session(prompt, system_prompt, callback, session_id, model=None):
        await callback({})
        return {"success": True, "message": "m2", "token_info": None, "session_id": None}

    class H2:
        send_message = staticmethod(send_no_session)

    ctx.claude_handler = H2()
    await chat_actions.chat(ctx, ws, {"prompt": "y", "provider": "claude"})
    assert "claude" not in room.get("provider_sessions", {})


@pytest.mark.asyncio
async def test_load_from_dict_restores_session_retention(tmp_path, monkeypatch):
    """실제 ContextHandler로 load_from_dict → chat 흐름에서 session_retention 유지 검증"""
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

    # 실제 ContextHandler 사용
    ctx.context_handler = ContextHandler()
    ctx.token_usage_handler = type(
        "T", (), {"add_usage": lambda *a, **k: None, "get_formatted_summary": lambda *a, **k: {}}
    )()
    ctx.sessions = {}
    ctx.websocket_to_session = {}

    ws = FakeWS()
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: 70)

    # 1. session_retention=True 설정 후 context를 dict로 저장
    ctx.context_handler.set_session_retention(True)
    saved_context = ctx.context_handler.get_context()
    assert saved_context.get("session_retention") is True

    # 2. 새 ContextHandler에서 load_from_dict로 복원
    ctx.context_handler = ContextHandler()
    ctx.context_handler.load_from_dict(saved_context)

    # 3. session_retention이 복원되었는지 확인
    restored_ctx = ctx.context_handler.get_context()
    assert restored_ctx.get("session_retention") is True

    # 4. chat 호출 시 session_id가 유지되는지 확인
    captured_session_ids = []

    async def capture_send(prompt, system_prompt, callback, session_id, model=None):
        captured_session_ids.append(session_id)
        await callback({})
        return {"success": True, "message": "resp", "token_info": None, "session_id": "NEW_SESSION"}

    class CaptureHandler:
        send_message = staticmethod(capture_send)

    ctx.claude_handler = CaptureHandler()
    ctx.droid_handler = None
    ctx.gemini_handler = None

    # 첫 번째 chat: session_id=None 전달 (새 세션)
    await chat_actions.chat(ctx, ws, {"prompt": "first", "provider": "claude"})
    assert captured_session_ids[-1] is None

    # 두 번째 chat: session_id="NEW_SESSION" 전달 (세션 유지)
    await chat_actions.chat(ctx, ws, {"prompt": "second", "provider": "claude"})
    assert captured_session_ids[-1] == "NEW_SESSION"

    # 5. session_retention=False로 변경 후 다시 load_from_dict
    ctx.context_handler.set_session_retention(False)
    saved_off = ctx.context_handler.get_context()

    ctx.context_handler = ContextHandler()
    ctx.context_handler.load_from_dict(saved_off)
    assert ctx.context_handler.get_context().get("session_retention") is False
