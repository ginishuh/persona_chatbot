"""HTTP 세션/사용자 격리 관련 최소 검증 (user_id 기반)."""

import os
import tempfile

import jwt
import pytest

from server.handlers.db_handler import DBHandler


@pytest.mark.asyncio
async def test_db_room_isolation_by_user_id():
    """같은 room_id라도 user_id가 다르면 서로의 데이터가 섞이지 않는다."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    try:
        db = DBHandler(db_path)
        await db.initialize()

        user_a = await db.create_user("alice", "alice@example.com", "hash")
        user_b = await db.create_user("bob", "bob@example.com", "hash")
        await db.approve_user(user_a, user_a)
        await db.approve_user(user_b, user_b)

        room_id = "shared"
        await db.upsert_room(room_id, user_a, "Alice Room", None)
        await db.upsert_room(room_id, user_b, "Bob Room", None)
        await db.save_message(room_id, "user", "안녕 Alice", user_a)
        await db.save_message(room_id, "user", "안녕 Bob", user_b)

        room_for_a = await db.get_room(room_id, user_a)
        room_for_b = await db.get_room(room_id, user_b)
        assert room_for_a["title"] == "Alice Room"
        assert room_for_b["title"] == "Bob Room"

        msgs_a = await db.list_messages(room_id, user_a)
        msgs_b = await db.list_messages(room_id, user_b)
        assert [m["content"] for m in msgs_a] == ["안녕 Alice"]
        assert [m["content"] for m in msgs_b] == ["안녕 Bob"]

        await db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_issue_token_includes_user_id(monkeypatch):
    """신규 토큰에는 user_id와 session_key가 모두 포함된다."""
    monkeypatch.setenv("APP_JWT_SECRET", "test_secret")  # pragma: allowlist secret
    import importlib

    import server.websocket_server as ws

    importlib.reload(ws)
    token, _ = ws._issue_token(ttl_seconds=3600, typ="access", session_key="user:test", user_id=42)
    payload = jwt.decode(token, options={"verify_signature": False})
    assert payload["session_key"] == "user:test"
    assert payload["user_id"] == 42


def test_issue_token_without_user_id(monkeypatch):
    """user_id 없이 발급하면 session_key만 포함되고 user_id는 빠진다."""
    monkeypatch.setenv("APP_JWT_SECRET", "test_secret2")  # pragma: allowlist secret
    import importlib

    import server.websocket_server as ws

    importlib.reload(ws)
    token, _ = ws._issue_token(ttl_seconds=3600, typ="access", session_key="user:test")
    payload = jwt.decode(token, options={"verify_signature": False})
    assert payload["session_key"] == "user:test"
    assert "user_id" not in payload
