import json
from pathlib import Path

import pytest

import server.websocket_server as ws_server
from server.core.app_context import AppContext
from server.handlers.context_handler import ContextHandler


class DummyWebSocket:
    """테스트용 WebSocket 더미 - send 호출 결과를 기록한다."""

    def __init__(self):
        self.sent: list[str] = []

    async def send(self, message: str):
        self.sent.append(message)


@pytest.fixture
def app_ctx(tmp_path: Path) -> AppContext:
    """핵심 컨텍스트 의존성을 최소 구성한 테스트용 AppContext."""

    ctx = AppContext(
        project_root=tmp_path,
        bind_host="127.0.0.1",
        login_required=False,
        jwt_secret="",
        jwt_algorithm="HS256",
        access_ttl_seconds=1,
        refresh_ttl_seconds=1,
        login_username="",
        login_rate_limit_max_attempts=5,
        login_rate_limit_window_seconds=60,
        token_expired_grace_seconds=60,
    )
    ctx.context_handler = ContextHandler()
    return ctx


@pytest.mark.asyncio
async def test_set_and_get_context_roundtrip(app_ctx: AppContext):
    """set_context → get_context 흐름이 성공적으로 왕복되는지 검증한다."""

    ws_server.APP_CTX = app_ctx
    dummy_ws = DummyWebSocket()

    payload = {
        "action": "set_context",
        "world": "테스트 월드",
        "situation": "시나리오",
        "user_character": "플레이어",
        "characters": [{"name": "NPC", "description": "친절한 안내자"}],
        "narrator_enabled": True,
        "narrator_mode": "moderate",
    }

    await ws_server.handle_message(dummy_ws, json.dumps(payload))

    assert dummy_ws.sent, "set_context 응답이 전송되어야 합니다."
    set_resp = json.loads(dummy_ws.sent[-1])
    assert set_resp["action"] == "set_context"
    assert set_resp["data"]["success"] is True
    ctx_after_set = set_resp["data"]["context"]
    assert ctx_after_set["world"] == "테스트 월드"
    assert ctx_after_set["narrator_enabled"] is True

    await ws_server.handle_message(dummy_ws, json.dumps({"action": "get_context"}))

    get_resp = json.loads(dummy_ws.sent[-1])
    assert get_resp["action"] == "get_context"
    assert get_resp["data"]["success"] is True
    ctx_after_get = get_resp["data"]["context"]
    assert ctx_after_get["world"] == "테스트 월드"
    assert ctx_after_get["narrator_enabled"] is True
