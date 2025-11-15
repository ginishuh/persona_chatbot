"""DB 마이그레이션(v4) 동작 테스트."""

import glob
import sqlite3
import tempfile
from pathlib import Path

import pytest

from server.handlers.db_handler import DBHandler


def _prepare_legacy_db(path: Path):
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        PRAGMA user_version = 2;
        CREATE TABLE sessions (session_key TEXT PRIMARY KEY);
        CREATE TABLE rooms (
            session_key TEXT,
            room_id TEXT PRIMARY KEY,
            title TEXT NOT NULL
        );
        CREATE TABLE messages (
            room_id TEXT,
            role TEXT,
            content TEXT
        );
        INSERT INTO rooms(session_key, room_id, title) VALUES('legacy-session', 'room1', '레거시 방');
        INSERT INTO messages(room_id, role, content) VALUES('room1', 'user', 'hello');
        """
    )
    conn.close()


@pytest.mark.asyncio
async def test_migration_creates_backup_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "chatbot.db"
        _prepare_legacy_db(db_path)

        handler = DBHandler(str(db_path))
        await handler.initialize()
        await handler.close()

        backups = glob.glob(str(db_path) + ".legacy-" + "*.bak")
        assert backups, "마이그레이션 전에 백업 파일이 생성되어야 합니다"

        # 새 스키마 확인 (rooms에 user_id 존재)
        conn = sqlite3.connect(db_path)
        cur = conn.execute("PRAGMA table_info(rooms)")
        columns = {row[1] for row in cur.fetchall()}
        conn.close()
        assert {"user_id", "room_id"}.issubset(columns)


@pytest.mark.asyncio
async def test_no_backup_when_already_v4():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "chatbot.db"
        handler = DBHandler(str(db_path))
        await handler.initialize()
        await handler.close()

        backups = glob.glob(str(db_path) + ".legacy-" + "*.bak")
        assert backups == []
