import asyncio
import json
from pathlib import Path

import jwt
import pytest

import server.websocket_server as ws_server
from server.core.app_context import AppContext
from server.handlers.context_handler import ContextHandler
from server.handlers.db_handler import DBHandler


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


@pytest.mark.asyncio
async def test_set_context_persists_to_db_and_reload(tmp_path: Path):
    """DB에 컨텍스트가 저장되고, 동일 토큰/room_id로 재로딩되는지 검증한다."""

    signer_value = tmp_path.name  # tmp 경로명 그대로 사용 (고정 비밀정보 아님)
    db_path = tmp_path / "chatbot.db"

    ctx = AppContext(
        project_root=tmp_path,
        bind_host="127.0.0.1",
        login_required=False,
        jwt_secret=signer_value,
        jwt_algorithm="HS256",
        access_ttl_seconds=1,
        refresh_ttl_seconds=1,
        login_username="",
        login_rate_limit_max_attempts=5,
        login_rate_limit_window_seconds=60,
        token_expired_grace_seconds=60,
    )
    ctx.context_handler = ContextHandler()
    ctx.loop = asyncio.get_running_loop()

    db_handler = DBHandler(str(db_path))
    await db_handler.initialize()
    ctx.db_handler = db_handler

    # 테스트 사용자 생성 및 JWT 발급
    user_id = await db_handler.create_user("alice", "alice@example.com", "hash")
    token = jwt.encode({"user_id": user_id, "typ": "access"}, signer_value, algorithm="HS256")

    ws_server.APP_CTX = ctx
    dummy_ws = DummyWebSocket()

    payload = {
        "action": "set_context",
        "room_id": "room-1",
        "world": "DB에 저장된 세계",
        "token": token,
    }

    await ws_server.handle_message(dummy_ws, json.dumps(payload))
    set_resp = json.loads(dummy_ws.sent[-1])
    assert set_resp["data"]["success"] is True

    # DB에 context가 저장되었는지 확인
    saved_room = await db_handler.get_room("room-1", user_id)
    assert saved_room is not None
    saved_ctx = json.loads(saved_room["context"])
    assert saved_ctx["world"] == "DB에 저장된 세계"

    # 새로운 ContextHandler로 교체 후 DB에서 로드되는지 확인
    ctx.context_handler = ContextHandler()
    ws_server.APP_CTX = ctx
    dummy_ws.sent.clear()

    await ws_server.handle_message(
        dummy_ws, json.dumps({"action": "get_context", "room_id": "room-1", "token": token})
    )

    get_resp = json.loads(dummy_ws.sent[-1])
    assert get_resp["action"] == "get_context"
    assert get_resp["data"]["success"] is True
    reloaded_ctx = get_resp["data"]["context"]
    assert reloaded_ctx["world"] == "DB에 저장된 세계"

    await db_handler.close()
