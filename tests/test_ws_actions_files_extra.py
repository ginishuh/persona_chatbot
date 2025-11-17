import json

import pytest

from server.core import session_manager as sm
from server.core.app_context import AppContext
from server.ws.actions import files as files_actions


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
    ctx.sessions = {}
    ctx.websocket_to_session = {}
    # create persona_data dir
    pd = tmp_path / "persona_data"
    pd.mkdir()
    (pd / "test.txt").write_text("hello")

    # minimal workspace_handler
    class WH:
        async def list_files(self, file_type=None):
            return {"files": ["test.txt"]}

        async def read_file(self, file_type, filename):
            return {"success": True, "content": "hello"}

        async def save_file(self, file_type, filename, content):
            return {"success": True}

        async def delete_file(self, file_type, filename):
            return {"success": True}

    ctx.workspace_handler = WH()
    return ctx


@pytest.mark.asyncio
async def test_list_files_and_read(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: None)

    await files_actions.list_workspace_files(ctx, ws, {})
    out = json.loads(ws.sent[-1])
    assert out["action"] == "list_workspace_files"

    await files_actions.load_workspace_file(ctx, ws, {"file_type": None, "filename": "test.txt"})
    r = json.loads(ws.sent[-1])
    assert r["data"]["success"] is True
    assert "hello" in r["data"]["content"]


@pytest.mark.asyncio
async def test_path_traversal_protection(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: None)

    # attempt to read outside project via traversal
    # read a file outside workspace via handler should be handled by workspace
    # simulate handler returning failure for invalid path
    class BadWH:
        async def read_file(self, file_type, filename):
            return {"success": False, "error": "invalid path"}

    ctx.workspace_handler = BadWH()
    await files_actions.load_workspace_file(
        ctx, ws, {"file_type": None, "filename": "../etc/passwd"}
    )
    out = json.loads(ws.sent[-1])
    assert out["data"]["success"] is False
