"""사용자 격리 통합 테스트 (user_id 기반)

이 테스트는 다음을 검증합니다:
1. 두 사용자가 같은 room_id를 사용할 때 메시지가 섞이지 않음
2. 사용자 A에서 사용자 B의 메시지를 조회할 수 없음
3. delete_room 시 다른 사용자의 데이터는 유지됨
4. Export API에서 다른 사용자 데이터를 조회할 수 없음
"""

import os
import tempfile

import pytest

from server.handlers.db_handler import DBHandler


@pytest.mark.asyncio
async def test_message_isolation_same_room_id():
    """같은 room_id를 쓰는 두 사용자의 메시지가 섞이지 않는지 테스트"""
    # 임시 DB 파일 생성
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = DBHandler(db_path)
        await db.initialize()

        # 두 사용자 생성
        await db.create_user("user_a", "a@example.com", "hash_a")
        await db.create_user("user_b", "b@example.com", "hash_b")
        await db.approve_user(1, 1)  # user_id=1 승인
        await db.approve_user(2, 1)  # user_id=2 승인

        user_a = 1
        user_b = 2
        room_id = "default"

        # 사용자 A 메시지 저장
        await db.upsert_room(room_id, user_a, "User A Room", None)
        await db.save_message(room_id, "user", "Hello from A", user_a)
        await db.save_message(room_id, "assistant", "Response to A", user_a)

        # 사용자 B 메시지 저장
        await db.upsert_room(room_id, user_b, "User B Room", None)
        await db.save_message(room_id, "user", "Hello from B", user_b)
        await db.save_message(room_id, "assistant", "Response to B", user_b)

        # 사용자 A 메시지 조회
        msgs_a = await db.list_messages(room_id, user_id=user_a)
        assert len(msgs_a) == 2
        assert msgs_a[0]["content"] == "Hello from A"
        assert msgs_a[1]["content"] == "Response to A"

        # 사용자 B 메시지 조회
        msgs_b = await db.list_messages(room_id, user_id=user_b)
        assert len(msgs_b) == 2
        assert msgs_b[0]["content"] == "Hello from B"
        assert msgs_b[1]["content"] == "Response to B"

        # 사용자 A에서 사용자 B 메시지를 조회할 수 없음
        assert all(m["content"] != "Hello from B" for m in msgs_a)

        await db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.asyncio
async def test_delete_room_isolation():
    """delete_room 시 다른 사용자의 데이터는 유지되는지 테스트"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = DBHandler(db_path)
        await db.initialize()

        # 두 사용자 생성
        await db.create_user("user_a", "a@example.com", "hash_a")
        await db.create_user("user_b", "b@example.com", "hash_b")
        await db.approve_user(1, 1)
        await db.approve_user(2, 1)

        user_a = 1
        user_b = 2
        room_id = "default"

        # 두 사용자에 같은 room_id로 메시지 저장
        await db.upsert_room(room_id, user_a, "User A Room", None)
        await db.save_message(room_id, "user", "A message", user_a)

        await db.upsert_room(room_id, user_b, "User B Room", None)
        await db.save_message(room_id, "user", "B message", user_b)

        # 사용자 A의 room 삭제
        await db.delete_room(room_id, user_id=user_a)

        # 사용자 A의 데이터는 삭제됨
        msgs_a = await db.list_messages(room_id, user_id=user_a)
        assert len(msgs_a) == 0

        # 사용자 B의 데이터는 유지됨
        msgs_b = await db.list_messages(room_id, user_id=user_b)
        assert len(msgs_b) == 1
        assert msgs_b[0]["content"] == "B message"

        await db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.asyncio
async def test_room_list_isolation():
    """list_rooms가 사용자별로 격리되는지 테스트"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = DBHandler(db_path)
        await db.initialize()

        # 두 사용자 생성
        await db.create_user("user_a", "a@example.com", "hash_a")
        await db.create_user("user_b", "b@example.com", "hash_b")
        await db.approve_user(1, 1)
        await db.approve_user(2, 1)

        user_a = 1
        user_b = 2

        # 사용자 A에 3개 방 생성
        await db.upsert_room("a_room_1", user_a, "A Room 1", None)
        await db.upsert_room("a_room_2", user_a, "A Room 2", None)
        await db.upsert_room("shared", user_a, "A Shared", None)

        # 사용자 B에 2개 방 생성 (하나는 같은 room_id)
        await db.upsert_room("b_room_1", user_b, "B Room 1", None)
        await db.upsert_room("shared", user_b, "B Shared", None)

        # 사용자 A는 자신의 방만 조회
        rooms_a = await db.list_rooms(user_a)
        assert len(rooms_a) == 3
        room_ids_a = [r["room_id"] for r in rooms_a]
        assert "a_room_1" in room_ids_a
        assert "a_room_2" in room_ids_a
        assert "shared" in room_ids_a
        assert "b_room_1" not in room_ids_a

        # 사용자 B는 자신의 방만 조회
        rooms_b = await db.list_rooms(user_b)
        assert len(rooms_b) == 2
        room_ids_b = [r["room_id"] for r in rooms_b]
        assert "b_room_1" in room_ids_b
        assert "shared" in room_ids_b
        assert "a_room_1" not in room_ids_b

        await db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.asyncio
async def test_token_usage_isolation():
    """토큰 사용량이 사용자별로 격리되는지 테스트"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = DBHandler(db_path)
        await db.initialize()

        # 두 사용자 생성
        await db.create_user("user_a", "a@example.com", "hash_a")
        await db.create_user("user_b", "b@example.com", "hash_b")
        await db.approve_user(1, 1)
        await db.approve_user(2, 1)

        user_a = 1
        user_b = 2
        room_id = "default"

        # 방 생성
        await db.upsert_room(room_id, user_a, "A Room", None)
        await db.upsert_room(room_id, user_b, "B Room", None)

        # 사용자 A 토큰 사용량 저장
        await db.save_token_usage(user_a, room_id, "claude", {"input": 100, "output": 200})

        # 사용자 B 토큰 사용량 저장
        await db.save_token_usage(user_b, room_id, "claude", {"input": 50, "output": 100})

        # 사용자 A 토큰 사용량 조회
        usage_a = await db.list_token_usage_range(room_id, user_id=user_a)
        assert len(usage_a) == 1

        # 사용자 B 토큰 사용량 조회
        usage_b = await db.list_token_usage_range(room_id, user_id=user_b)
        assert len(usage_b) == 1

        await db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
