import json

import pytest

from server.core.app_context import AppContext
from server.handlers.workspace_handler import WorkspaceHandler
from server.ws.actions import files as files_actions
from server.ws.actions import rooms as rooms_actions


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
    ctx.workspace_handler = WorkspaceHandler(str(tmp_path / "persona_data"))
    ctx.db_handler = None
    return ctx


@pytest.mark.asyncio
async def test_list_workspace_files_action(tmp_path):
    ctx = make_ctx(tmp_path)
    # create a world file
    await ctx.workspace_handler.save_file("world", "w1", "content")

    ws = FakeWS()
    await files_actions.list_workspace_files(ctx, ws, {"file_type": "world"})
    assert ws.sent
    msg = json.loads(ws.sent[-1])
    assert msg["action"] == "list_workspace_files"
    assert msg["data"]["success"] is True


@pytest.mark.asyncio
async def test_room_list_auth_and_noauth(monkeypatch, tmp_path):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()

    # unauthenticated
    monkeypatch.setattr("server.core.session_manager.get_user_id_from_token", lambda c, d: None)
    await rooms_actions.room_list(ctx, ws, {})
    msg = json.loads(ws.sent[-1])
    assert msg["action"] == "room_list"
    assert msg["data"]["success"] is False

    # authenticated with DB
    async def fake_list_rooms(uid):
        return [{"room_id": "r1", "title": "R1", "created_at": "2020-01-01T00:00:00"}]

    ctx.db_handler = type("D", (), {"list_rooms": staticmethod(fake_list_rooms)})
    monkeypatch.setattr("server.core.session_manager.get_user_id_from_token", lambda c, d: 9)
    ws2 = FakeWS()
    await rooms_actions.room_list(ctx, ws2, {})
    msg2 = json.loads(ws2.sent[-1])
    assert msg2["action"] == "room_list"
    assert msg2["data"]["success"] is True
    assert msg2["data"]["rooms"]
