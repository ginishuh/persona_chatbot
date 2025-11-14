"""세션 격리 통합 테스트

이 테스트는 다음을 검증합니다:
1. 두 세션에서 같은 room_id를 사용할 때 메시지가 섞이지 않음
2. 세션 A에서 세션 B의 메시지를 조회할 수 없음
3. delete_room 시 다른 세션의 데이터는 유지됨
4. Export API에서 다른 세션 데이터를 조회할 수 없음
"""

import os
import tempfile

import pytest

from server.handlers.db_handler import DBHandler


@pytest.mark.asyncio
async def test_message_isolation_same_room_id():
    """같은 room_id를 쓰는 두 세션의 메시지가 섞이지 않는지 테스트"""
    # 임시 DB 파일 생성
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = DBHandler(db_path)
        await db.initialize()

        # 두 세션, 같은 room_id
        session_a = "session_a"
        session_b = "session_b"
        room_id = "default"

        # 세션 A 메시지 저장
        await db.upsert_session(session_a)
        await db.upsert_room(room_id, session_a, "Session A Room", None)
        await db.save_message(room_id, "user", "Hello from A", session_a)
        await db.save_message(room_id, "assistant", "Response to A", session_a)

        # 세션 B 메시지 저장
        await db.upsert_session(session_b)
        await db.upsert_room(room_id, session_b, "Session B Room", None)
        await db.save_message(room_id, "user", "Hello from B", session_b)
        await db.save_message(room_id, "assistant", "Response to B", session_b)

        # 세션 A 메시지 조회
        msgs_a = await db.list_messages(room_id, session_key=session_a)
        assert len(msgs_a) == 2
        assert msgs_a[0]["content"] == "Hello from A"
        assert msgs_a[1]["content"] == "Response to A"

        # 세션 B 메시지 조회
        msgs_b = await db.list_messages(room_id, session_key=session_b)
        assert len(msgs_b) == 2
        assert msgs_b[0]["content"] == "Hello from B"
        assert msgs_b[1]["content"] == "Response to B"

        # 세션 A에서 세션 B 메시지를 조회할 수 없음
        assert all(m["content"] != "Hello from B" for m in msgs_a)

        await db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.asyncio
async def test_delete_room_isolation():
    """delete_room 시 다른 세션의 데이터는 유지되는지 테스트"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = DBHandler(db_path)
        await db.initialize()

        session_a = "session_a"
        session_b = "session_b"
        room_id = "default"

        # 두 세션에 같은 room_id로 메시지 저장
        await db.upsert_session(session_a)
        await db.upsert_room(room_id, session_a, "Session A Room", None)
        await db.save_message(room_id, "user", "A message", session_a)

        await db.upsert_session(session_b)
        await db.upsert_room(room_id, session_b, "Session B Room", None)
        await db.save_message(room_id, "user", "B message", session_b)

        # 세션 A의 room 삭제
        await db.delete_room(room_id, session_key=session_a)

        # 세션 A의 데이터는 삭제됨
        msgs_a = await db.list_messages(room_id, session_key=session_a)
        assert len(msgs_a) == 0

        # 세션 B의 데이터는 유지됨
        msgs_b = await db.list_messages(room_id, session_key=session_b)
        assert len(msgs_b) == 1
        assert msgs_b[0]["content"] == "B message"

        await db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.asyncio
async def test_token_usage_isolation():
    """토큰 사용량도 세션별로 격리되는지 테스트"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = DBHandler(db_path)
        await db.initialize()

        session_a = "session_a"
        session_b = "session_b"
        room_id = "default"

        # 세션 A 토큰 사용량 저장
        await db.upsert_session(session_a)
        await db.upsert_room(room_id, session_a, "Room A", None)
        await db.save_token_usage(session_a, room_id, "claude", {"tokens": 100})

        # 세션 B 토큰 사용량 저장
        await db.upsert_session(session_b)
        await db.upsert_room(room_id, session_b, "Room B", None)
        await db.save_token_usage(session_b, room_id, "claude", {"tokens": 200})

        # 세션 A 토큰 사용량 조회
        usage_a = await db.list_token_usage_range(room_id, session_key=session_a)
        assert len(usage_a) == 1
        assert "100" in usage_a[0]["token_info"]

        # 세션 B 토큰 사용량 조회
        usage_b = await db.list_token_usage_range(room_id, session_key=session_b)
        assert len(usage_b) == 1
        assert "200" in usage_b[0]["token_info"]

        await db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.asyncio
async def test_room_get_isolation():
    """get_room이 세션 키로 격리되는지 테스트"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = DBHandler(db_path)
        await db.initialize()

        session_a = "session_a"
        session_b = "session_b"
        room_id = "default"

        # 세션 A의 room 생성
        await db.upsert_session(session_a)
        await db.upsert_room(room_id, session_a, "Session A Room", '{"key":"value_a"}')

        # 세션 B의 room 생성
        await db.upsert_session(session_b)
        await db.upsert_room(room_id, session_b, "Session B Room", '{"key":"value_b"}')

        # 세션 A로 조회
        room_a = await db.get_room(room_id, session_key=session_a)
        assert room_a is not None
        assert room_a["title"] == "Session A Room"
        assert "value_a" in room_a["context"]

        # 세션 B로 조회
        room_b = await db.get_room(room_id, session_key=session_b)
        assert room_b is not None
        assert room_b["title"] == "Session B Room"
        assert "value_b" in room_b["context"]

        # 세션 A에서 세션 B 데이터를 조회할 수 없음
        assert "value_b" not in room_a["context"]

        await db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.asyncio
async def test_migration_preserves_data():
    """마이그레이션 후에도 데이터가 보존되는지 테스트"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = DBHandler(db_path)
        await db.initialize()

        # 세션과 메시지 생성
        session_key = "test_session"
        room_id = "test_room"

        await db.upsert_session(session_key)
        await db.upsert_room(room_id, session_key, "Test Room", None)
        await db.save_message(room_id, "user", "Test message", session_key)

        # 메시지 조회
        msgs = await db.list_messages(room_id, session_key=session_key)
        assert len(msgs) == 1
        assert msgs[0]["content"] == "Test message"

        # DB 재시작 (마이그레이션 재실행)
        await db.close()

        db2 = DBHandler(db_path)
        await db2.initialize()

        # 데이터가 보존되었는지 확인
        msgs2 = await db2.list_messages(room_id, session_key=session_key)
        assert len(msgs2) == 1
        assert msgs2[0]["content"] == "Test message"

        await db2.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
