import json

import pytest

from server.core.app_context import AppContext
from server.ws.actions import files as files_actions


class FakeWS:
    def __init__(self):
        self.sent = []

    async def send(self, msg):
        self.sent.append(msg)


def make_ctx_with_wh(tmp_path, wh):
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
    ctx.workspace_handler = wh
    return ctx


@pytest.mark.asyncio
async def test_save_and_delete_workspace_file_success(tmp_path):
    class WH:
        async def save_file(self, file_type, filename, content):
            return {"success": True}

        async def delete_file(self, file_type, filename):
            return {"success": True}

    ctx = make_ctx_with_wh(tmp_path, WH())
    ws = FakeWS()

    await files_actions.save_workspace_file(
        ctx, ws, {"file_type": "preset", "filename": "p1", "content": "c"}
    )
    out = json.loads(ws.sent[-1])
    assert out["action"] == "save_workspace_file"
    assert out["data"]["success"] is True

    await files_actions.delete_workspace_file(ctx, ws, {"file_type": "preset", "filename": "p1"})
    out2 = json.loads(ws.sent[-1])
    assert out2["action"] == "delete_workspace_file"
    assert out2["data"]["success"] is True


@pytest.mark.asyncio
async def test_save_workspace_file_failure_returns_error(tmp_path):
    class WH:
        async def save_file(self, file_type, filename, content):
            return {"success": False, "error": "no space"}

    ctx = make_ctx_with_wh(tmp_path, WH())
    ws = FakeWS()

    await files_actions.save_workspace_file(
        ctx, ws, {"file_type": "preset", "filename": "pX", "content": "c"}
    )
    out = json.loads(ws.sent[-1])
    assert out["data"]["success"] is False
    assert out["data"]["error"] == "no space"


@pytest.mark.asyncio
async def test_load_and_list_workspace_files(tmp_path):
    class WH:
        async def list_files(self, file_type=None):
            return {"files": ["a.json", "b.json"]}

        async def read_file(self, file_type, filename):
            return {"success": True, "content": "ok"}

    ctx = make_ctx_with_wh(tmp_path, WH())
    ws = FakeWS()

    await files_actions.list_workspace_files(ctx, ws, {"file_type": "preset"})
    list_msg = json.loads(ws.sent[-1])
    assert list_msg["action"] == "list_workspace_files"
    assert "files" in list_msg["data"]

    await files_actions.load_workspace_file(ctx, ws, {"file_type": "preset", "filename": "a.json"})
    r = json.loads(ws.sent[-1])
    assert r["data"]["success"] is True
    assert r["data"]["content"] == "ok"


@pytest.mark.asyncio
async def test_load_workspace_file_failure(tmp_path):
    class WH:
        async def read_file(self, file_type, filename):
            return {"success": False, "error": "not found"}

    ctx = make_ctx_with_wh(tmp_path, WH())
    ws = FakeWS()

    await files_actions.load_workspace_file(ctx, ws, {"file_type": "preset", "filename": "nope"})
    out = json.loads(ws.sent[-1])
    assert out["data"]["success"] is False
    assert out["data"]["error"] == "not found"
