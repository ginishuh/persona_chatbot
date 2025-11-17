import json

import pytest

from server.handlers.db_handler import DBHandler


@pytest.mark.asyncio
async def test_dbhandler_crud_flow(tmp_path):
    db_file = str(tmp_path / "data" / "chatbot.db")
    db = DBHandler(db_file)

    # initialize should create file and setup schema
    await db.initialize()

    # create a user
    user_id = await db.create_user("u1", "u1@example.com", "phash")
    assert isinstance(user_id, int)

    # fetch by username and by id
    u = await db.get_user_by_username("u1")
    assert u is not None and u["username"] == "u1"
    u2 = await db.get_user_by_id(user_id)
    assert u2 is not None and u2["user_id"] == user_id

    # create admin user
    admin_id = await db.create_admin_user("adminx", "a@example.com", "h")
    assert isinstance(admin_id, int)

    # upsert a room and retrieve it
    await db.upsert_room("room1", user_id, "Title 1", json.dumps({"a": 1}))
    room = await db.get_room("room1", user_id)
    assert room is not None and room["room_id"] == "room1"

    # list rooms
    rooms = await db.list_rooms(user_id)
    assert any(r["room_id"] == "room1" for r in rooms)

    # save message and list messages
    await db.save_message("room1", "user", "hello", user_id)
    msgs = await db.list_messages("room1", user_id)
    assert any(m["content"] == "hello" for m in msgs)

    # save token usage and list
    await db.save_token_usage(user_id, "room1", "claude", {"i": 1})
    toks = await db.list_token_usage_range("room1", user_id)
    assert any(t["provider"] == "claude" for t in toks)

    # approve user
    ok = await db.approve_user(user_id, admin_id)
    assert ok is True

    # list all rooms (admin)
    all_rooms = await db.list_all_rooms()
    assert any(r["room_id"] == "room1" for r in all_rooms)

    # delete room and ensure deletion
    await db.delete_room("room1", user_id)
    r_none = await db.get_room("room1", user_id)
    assert r_none is None

    await db.close()
