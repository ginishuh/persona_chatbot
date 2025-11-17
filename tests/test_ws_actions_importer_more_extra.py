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
async def test_duplicate_policy_skip_and_add(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: 99)

    # create a room with id 'rdup' and insert a message so duplicate detection works
    _, sess = sm.get_or_create_session(ctx, ws, 99)
    _, room = sm.get_room(ctx, sess, "rdup")
    room["history"].add_user_message("dup")

    payload = {
        "export_type": "single_room",
        "room": {
            "room_id": "rdup",
            "messages": [
                {"role": "user", "content": "dup"},
                {"role": "assistant", "content": "new"},
            ],
        },
    }

    # skip policy should avoid importing the duplicate message
    await importer_actions.import_data(ctx, ws, {"json_data": payload, "duplicate_policy": "skip"})
    res = json.loads(ws.sent[-1])
    assert res["data"]["messages_imported"] == 1

    # add policy should import both
    await importer_actions.import_data(ctx, ws, {"json_data": payload, "duplicate_policy": "add"})
    res2 = json.loads(ws.sent[-1])
    assert res2["data"]["messages_imported"] == 2


@pytest.mark.asyncio
async def test_import_handles_exceptions_in_single_room(tmp_path, monkeypatch):
    ctx = make_ctx(tmp_path)
    ws = FakeWS()
    monkeypatch.setattr(sm, "get_user_id_from_token", lambda c, d: 11)

    # create a room object with messages, but patch ctx.db_handler methods to raise
    class DB:
        async def upsert_room(self, rid, user_id, title, context):
            raise RuntimeError("boom")

        async def save_message(self, rid, role, content, user_id):
            raise RuntimeError("boom2")

    ctx.db_handler = DB()

    payload = {"room": {"room_id": "rX", "messages": [{"role": "assistant", "content": "a"}]}}
    await importer_actions.import_data(ctx, ws, {"json_data": payload})
    out = json.loads(ws.sent[-1])
    assert out["data"]["success"] is True
