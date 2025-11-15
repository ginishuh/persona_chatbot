"""DB 마이그레이션 테스트 (v0 → v1)

구버전 스키마에서 신버전 스키마로의 자동 마이그레이션을 검증합니다.
"""

import os
import sqlite3
import tempfile

import pytest

from server.handlers.db_handler import DBHandler


@pytest.mark.asyncio
async def test_migration_from_v0_single_pk():
    """v0 스키마 (단일 PK room_id)에서 v1 (복합 PK session_key, room_id)로 마이그레이션"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        # 1. 구버전 스키마 수동 생성 (단일 PK)
        conn = sqlite3.connect(db_path)
        conn.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE sessions (
                session_key TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 구버전: 단일 PK (room_id만)
            CREATE TABLE rooms (
                room_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 구버전: session_key 없음
            CREATE TABLE messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role in ('user','assistant')),
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE token_usage (
                usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_key TEXT NOT NULL,
                room_id TEXT,
                provider TEXT NOT NULL,
                token_info TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # 2. 구버전 데이터 추가
        conn.execute("INSERT INTO sessions(session_key) VALUES(?)", ("test_session",))
        conn.execute(
            "INSERT INTO rooms(room_id, title, context) VALUES(?, ?, ?)",
            ("room1", "테스트 방", '{"world": "판타지"}'),
        )
        conn.execute(
            "INSERT INTO messages(room_id, role, content) VALUES(?, ?, ?)",
            ("room1", "user", "안녕하세요"),
        )
        conn.execute(
            "INSERT INTO messages(room_id, role, content) VALUES(?, ?, ?)",
            ("room1", "assistant", "반갑습니다"),
        )
        conn.commit()
        conn.close()

        # 3. DBHandler로 열어서 자동 마이그레이션 실행
        db = DBHandler(db_path)
        await db.initialize()

        # 4. 마이그레이션 검증: rooms 테이블 복합 PK 확인
        cur = await db._conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='rooms'"
        )
        row = await cur.fetchone()
        assert row is not None
        table_sql = row[0]
        assert "PRIMARY KEY (session_key, room_id)" in table_sql

        # 5. 마이그레이션 검증: messages 테이블 session_key 컬럼 확인
        cur = await db._conn.execute("PRAGMA table_info(messages)")
        columns = await cur.fetchall()
        column_names = [col[1] for col in columns]
        assert "session_key" in column_names

        # 6. 데이터 보존 확인 (legacy session_key로 이동)
        msgs = await db.list_messages("room1", session_key="legacy")
        assert len(msgs) == 2
        assert msgs[0]["content"] == "안녕하세요"
        assert msgs[1]["content"] == "반갑습니다"

        # 7. upsert_room이 정상 동작하는지 확인 (복합 PK)
        await db.upsert_room("room2", "new_session", "새 방", '{"test": "data"}')
        room = await db.get_room("room2", "new_session")
        assert room is not None
        assert room["title"] == "새 방"

        # 8. 기존 room을 새 session_key로 upsert 가능 (충돌 없음)
        await db.upsert_room("room1", "another_session", "다른 세션 방", None)
        room2 = await db.get_room("room1", "another_session")
        assert room2 is not None
        assert room2["title"] == "다른 세션 방"

        await db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.asyncio
async def test_migration_already_migrated():
    """이미 마이그레이션된 DB는 재마이그레이션하지 않음"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        # 1. 이미 v1 스키마로 생성
        db = DBHandler(db_path)
        await db.initialize()

        # 2. 데이터 추가
        await db.upsert_session("session1")
        await db.upsert_room("room1", "session1", "방1", None)
        await db.save_message("room1", "user", "메시지", "session1")

        await db.close()

        # 3. 다시 열어서 마이그레이션 시도 (이미 완료되어 skip)
        db2 = DBHandler(db_path)
        await db2.initialize()

        # 4. 데이터가 그대로 유지되는지 확인
        msgs = await db2.list_messages("room1", session_key="session1")
        assert len(msgs) == 1
        assert msgs[0]["content"] == "메시지"

        await db2.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.asyncio
async def test_migration_with_orphan_messages():
    """고아 메시지 (room이 없는)는 'legacy' session으로 이동"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        # 1. 구버전 스키마 생성
        conn = sqlite3.connect(db_path)
        conn.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE sessions (
                session_key TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE rooms (
                room_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # 2. room 없이 메시지만 추가 (고아 메시지)
        conn.execute(
            "INSERT INTO messages(room_id, role, content) VALUES(?, ?, ?)",
            ("orphan_room", "user", "고아 메시지"),
        )
        conn.commit()
        conn.close()

        # 3. 마이그레이션 실행
        db = DBHandler(db_path)
        await db.initialize()

        # 4. 고아 메시지가 'legacy' session으로 이동했는지 확인
        msgs = await db.list_messages("orphan_room", session_key="legacy")
        assert len(msgs) == 1
        assert msgs[0]["content"] == "고아 메시지"

        await db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.asyncio
async def test_migration_preserves_existing_session_keys():
    """기존 session_key 값이 있는 경우 유지되는지 확인"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        # 1. 구버전 스키마 생성 (session_key 컬럼 있음, 단일 PK)
        conn = sqlite3.connect(db_path)
        conn.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE sessions (
                session_key TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 구버전: session_key 컬럼은 있지만 단일 PK (room_id만)
            CREATE TABLE rooms (
                room_id TEXT PRIMARY KEY,
                session_key TEXT,
                title TEXT NOT NULL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # 2. 세션 및 데이터 추가 (각 room이 다른 session_key 가짐)
        conn.execute("INSERT INTO sessions(session_key) VALUES(?)", ("session_a",))
        conn.execute("INSERT INTO sessions(session_key) VALUES(?)", ("session_b",))

        conn.execute(
            "INSERT INTO rooms(room_id, session_key, title, context) VALUES(?, ?, ?, ?)",
            ("room1", "session_a", "세션A의 방1", '{"owner": "A"}'),
        )
        conn.execute(
            "INSERT INTO rooms(room_id, session_key, title, context) VALUES(?, ?, ?, ?)",
            ("room2", "session_b", "세션B의 방2", '{"owner": "B"}'),
        )
        # session_key가 NULL인 방도 추가
        conn.execute(
            "INSERT INTO rooms(room_id, title) VALUES(?, ?)",
            ("room3", "세션키 없는 방3"),
        )

        conn.execute(
            "INSERT INTO messages(room_id, role, content) VALUES(?, ?, ?)",
            ("room1", "user", "세션A 메시지"),
        )
        conn.execute(
            "INSERT INTO messages(room_id, role, content) VALUES(?, ?, ?)",
            ("room2", "user", "세션B 메시지"),
        )
        conn.commit()
        conn.close()

        # 3. 마이그레이션 실행
        db = DBHandler(db_path)
        await db.initialize()

        # 4. rooms 테이블 복합 PK 확인
        cur = await db._conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='rooms'"
        )
        row = await cur.fetchone()
        assert row is not None
        assert "PRIMARY KEY (session_key, room_id)" in row[0]

        # 5. 기존 session_key가 유지되었는지 확인
        room1 = await db.get_room("room1", "session_a")
        assert room1 is not None
        assert room1["title"] == "세션A의 방1"
        assert room1["session_key"] == "session_a"

        room2 = await db.get_room("room2", "session_b")
        assert room2 is not None
        assert room2["title"] == "세션B의 방2"
        assert room2["session_key"] == "session_b"

        # 6. session_key가 NULL이었던 방은 'legacy'로 이동
        room3 = await db.get_room("room3", "legacy")
        assert room3 is not None
        assert room3["title"] == "세션키 없는 방3"
        assert room3["session_key"] == "legacy"

        # 7. 잘못된 session_key로는 조회 불가
        room1_wrong = await db.get_room("room1", "session_b")
        assert room1_wrong is None

        # 8. messages도 올바른 session_key로 이동했는지 확인
        msgs_a = await db.list_messages("room1", session_key="session_a")
        assert len(msgs_a) == 1
        assert msgs_a[0]["content"] == "세션A 메시지"

        msgs_b = await db.list_messages("room2", session_key="session_b")
        assert len(msgs_b) == 1
        assert msgs_b[0]["content"] == "세션B 메시지"

        await db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.asyncio
async def test_migration_user_version():
    """user_version이 올바르게 설정되는지 확인"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        # 1. 구버전 DB 생성
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA user_version = 0")
        conn.executescript(
            """
            CREATE TABLE sessions (session_key TEXT PRIMARY KEY);
            CREATE TABLE rooms (room_id TEXT PRIMARY KEY, title TEXT);
            CREATE TABLE messages (message_id INTEGER PRIMARY KEY, room_id TEXT, role TEXT, content TEXT);
            CREATE TABLE token_usage (usage_id INTEGER PRIMARY KEY, session_key TEXT, room_id TEXT, provider TEXT, token_info TEXT);
            """
        )
        conn.commit()
        conn.close()

        # 2. 마이그레이션 실행
        db = DBHandler(db_path)
        await db.initialize()

        # 3. user_version이 3으로 업데이트되었는지 확인 (v0 → v1 → v2 → v3)
        cur = await db._conn.execute("PRAGMA user_version")
        row = await cur.fetchone()
        assert row[0] == 3

        await db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
