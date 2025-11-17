import json

import pytest

from server.core import session_manager as sm
from server.core.app_context import AppContext
from server.ws.actions import importer as importer_actions


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
    ctx.db_handler = None
    ctx.sessions = {}
    ctx.websocket_to_session = {}
    return ctx


@pytest.mark.asyncio
async def test_import_requires_auth(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: None)

    await importer_actions.import_data(ctx, ws, {})
    out = json.loads(ws.sent[-1])
    assert out["action"] == "import_data"
    assert out["data"]["success"] is False


@pytest.mark.asyncio
async def test_import_single_room_and_full_backup(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: 5)

    payload = {
        "export_type": "single_room",
        "room": {
            "room_id": "r1",
            "title": "T",
            "messages": [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "ok"},
            ],
        },
    }

    await importer_actions.import_data(ctx, ws, {"json_data": payload})
    res = json.loads(ws.sent[-1])
    assert res["action"] == "import_data"
    assert res["data"]["success"] is True
    assert res["data"]["rooms_imported"] == 1
    assert res["data"]["messages_imported"] == 2

    # full backup with two rooms
    rooms_payload = {
        "export_type": "full_backup",
        "rooms": [
            {"room_id": "ra", "messages": [{"role": "assistant", "content": "a"}]},
            {
                "room_id": "rb",
                "messages": [{"role": "user", "content": "b1"}, {"role": "user", "content": "b2"}],
            },
        ],
    }

    await importer_actions.import_data(ctx, ws, {"json_data": rooms_payload})
    res2 = json.loads(ws.sent[-1])
    assert res2["data"]["rooms_imported"] == 2
    assert res2["data"]["messages_imported"] == 3
