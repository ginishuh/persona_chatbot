"""다중 기기 동기화 통합 테스트

시나리오:
1. UUID 세션으로 채팅방 생성
2. 로그인하여 user:{username} 세션으로 마이그레이션
3. 다른 기기에서 동일 계정으로 로그인
4. 두 기기 모두 동일한 채팅방 목록 확인
"""

import json
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from server.handlers.db_handler import DBHandler


@pytest_asyncio.fixture
async def test_db():
    """테스트용 임시 DB"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DBHandler(str(db_path))
        await db.initialize()
        yield db
        await db.close()


@pytest.mark.asyncio
async def test_uuid_to_user_migration(test_db):
    """UUID 세션 → 로그인 전환 시 마이그레이션"""

    # 1. UUID 세션으로 채팅방 생성 (로그인 전)
    uuid_session = "test-uuid-123"
    await test_db.upsert_room("room1", uuid_session, "테스트 방 1", None)
    await test_db.upsert_room("room2", uuid_session, "테스트 방 2", None)
    await test_db.save_message("room1", "user", "안녕하세요")

    # 확인: UUID로 조회 가능
    rooms = await test_db.list_rooms(uuid_session)
    assert len(rooms) == 2

    # 2. 로그인 후 user:{username}으로 마이그레이션 시뮬레이션
    user_session = "user:testuser"
    old_rooms = await test_db.list_rooms(uuid_session)
    for room in old_rooms:
        await test_db.upsert_room(room["room_id"], user_session, room["title"], room["context"])

    # 3. 검증: user:{username}으로 조회 가능
    migrated_rooms = await test_db.list_rooms(user_session)
    assert len(migrated_rooms) == 2
    room_ids = {r["room_id"] for r in migrated_rooms}
    assert "room1" in room_ids
    assert "room2" in room_ids

    # 4. 메시지도 유지됨
    messages = await test_db.list_messages("room1")
    assert len(messages) == 1
    assert messages[0]["content"] == "안녕하세요"


@pytest.mark.asyncio
async def test_multi_device_same_user(test_db):
    """동일 사용자가 두 기기에서 로그인 (세션 공유)"""

    user_session = "user:alice"

    # 기기 1: 채팅방 생성
    await test_db.upsert_room("room_a", user_session, "Alice의 방 A", None)
    await test_db.save_message("room_a", "user", "기기 1에서 메시지")

    # 기기 2: 동일 user_session으로 조회
    rooms = await test_db.list_rooms(user_session)
    assert len(rooms) == 1
    assert rooms[0]["room_id"] == "room_a"

    # 기기 2: 메시지 추가
    await test_db.save_message("room_a", "assistant", "AI 응답")

    # 기기 1: 모든 메시지 조회 가능
    messages = await test_db.list_messages("room_a")
    assert len(messages) == 2
    assert messages[0]["content"] == "기기 1에서 메시지"
    assert messages[1]["content"] == "AI 응답"


@pytest.mark.asyncio
async def test_multi_user_isolation(test_db):
    """여러 사용자 데이터 격리 (마이그레이션 회귀 방지)"""

    # 사용자 A
    await test_db.upsert_room("room_a1", "user:alice", "Alice 방 1", None)
    await test_db.upsert_room("room_a2", "user:alice", "Alice 방 2", None)

    # 사용자 B
    await test_db.upsert_room("room_b1", "user:bob", "Bob 방 1", None)

    # 검증: 각자의 방만 조회
    alice_rooms = await test_db.list_rooms("user:alice")
    bob_rooms = await test_db.list_rooms("user:bob")

    assert len(alice_rooms) == 2
    assert len(bob_rooms) == 1

    alice_ids = {r["room_id"] for r in alice_rooms}
    bob_ids = {r["room_id"] for r in bob_rooms}

    assert "room_a1" in alice_ids
    assert "room_a2" in alice_ids
    assert "room_b1" in bob_ids
    assert "room_b1" not in alice_ids


@pytest.mark.asyncio
async def test_migration_only_current_session(test_db):
    """마이그레이션은 현재 세션만 (전체 덮어쓰기 방지)"""

    # 사용자 A의 UUID 세션
    uuid_a = "uuid-alice-device1"
    await test_db.upsert_room("room_a", uuid_a, "Alice 방", None)

    # 사용자 B의 UUID 세션
    uuid_b = "uuid-bob-device1"
    await test_db.upsert_room("room_b", uuid_b, "Bob 방", None)

    # Alice 로그인 → uuid_a만 마이그레이션
    old_rooms_a = await test_db.list_rooms(uuid_a)
    for room in old_rooms_a:
        await test_db.upsert_room(room["room_id"], "user:alice", room["title"], room["context"])

    # 검증: Alice는 자기 방만
    alice_rooms = await test_db.list_rooms("user:alice")
    assert len(alice_rooms) == 1
    assert alice_rooms[0]["room_id"] == "room_a"

    # 검증: Bob의 UUID 세션은 그대로
    bob_uuid_rooms = await test_db.list_rooms(uuid_b)
    assert len(bob_uuid_rooms) == 1
    assert bob_uuid_rooms[0]["room_id"] == "room_b"

    # Bob 로그인 → uuid_b만 마이그레이션
    old_rooms_b = await test_db.list_rooms(uuid_b)
    for room in old_rooms_b:
        await test_db.upsert_room(room["room_id"], "user:bob", room["title"], room["context"])

    # 검증: 각자 방 유지
    alice_final = await test_db.list_rooms("user:alice")
    bob_final = await test_db.list_rooms("user:bob")

    assert len(alice_final) == 1
    assert len(bob_final) == 1
    assert alice_final[0]["room_id"] == "room_a"
    assert bob_final[0]["room_id"] == "room_b"


@pytest.mark.asyncio
async def test_export_import_roundtrip(test_db):
    """Export → Import 라운드트립"""

    # 1. 원본 데이터 생성
    user_session = "user:testuser"
    await test_db.upsert_room("original", user_session, "원본 방", '{"world": "판타지"}')
    await test_db.save_message("original", "user", "원본 메시지 1")
    await test_db.save_message("original", "assistant", "원본 응답 1")

    # 2. Export 시뮬레이션 (single_room)
    room_data = await test_db.get_room("original")
    messages = await test_db.list_messages("original")

    export_data = {
        "version": "1.0",
        "export_type": "single_room",
        "room": {
            "room_id": room_data["room_id"],
            "title": room_data["title"],
            "context": json.loads(room_data["context"] or "{}"),
            "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
            "token_usage": [],
        },
    }

    # 3. Import 시뮬레이션 (다른 room_id로)
    imported_room = export_data["room"]
    new_room_id = "imported_room"
    context_str = json.dumps(imported_room["context"])

    await test_db.upsert_room(new_room_id, user_session, imported_room["title"], context_str)
    for msg in imported_room["messages"]:
        await test_db.save_message(new_room_id, msg["role"], msg["content"])

    # 4. 검증: 두 방 모두 존재
    rooms = await test_db.list_rooms(user_session)
    assert len(rooms) == 2

    # 5. Import된 방 내용 확인
    imported_messages = await test_db.list_messages(new_room_id)
    assert len(imported_messages) == 2
    assert imported_messages[0]["content"] == "원본 메시지 1"
    assert imported_messages[1]["content"] == "원본 응답 1"

    imported_room_data = await test_db.get_room(new_room_id)
    imported_context = json.loads(imported_room_data["context"])
    assert imported_context["world"] == "판타지"
