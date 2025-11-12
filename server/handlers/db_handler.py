import asyncio
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import aiosqlite


class DBHandler:
    """SQLite 비동기 핸들러 (aiosqlite)

    - DB 초기화/마이그레이션
    - rooms / messages / sessions / token_usage 기본 CRUD
    - 현재 단계: 스켈레톤(필수 최소 기능)
    """

    def __init__(self, db_path: str = "data/chatbot.db") -> None:
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None
        # write 작업 직렬화를 위한 락(간단 보장)
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """DB 파일 경로 생성, 연결, PRAGMA, 스키마 생성까지 수행."""
        Path(os.path.dirname(self.db_path) or ".").mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON;")
        await self._conn.execute("PRAGMA journal_mode = WAL;")
        await self._conn.commit()
        await self._migrate()

    async def _migrate(self) -> None:
        """최초 스키마 생성(간단 버전). user_version은 후속 버전에서 사용."""
        assert self._conn is not None
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_key TEXT PRIMARY KEY,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS rooms (
                room_id TEXT PRIMARY KEY,
                session_key TEXT NOT NULL,
                title TEXT NOT NULL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_key) REFERENCES sessions(session_key) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_rooms_session ON rooms(session_key);

            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role in ('user','assistant')),
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_messages_room ON messages(room_id);
            CREATE INDEX IF NOT EXISTS idx_messages_ts ON messages(timestamp);

            CREATE TABLE IF NOT EXISTS token_usage (
                usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_key TEXT NOT NULL,
                room_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                token_info TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_key) REFERENCES sessions(session_key) ON DELETE CASCADE,
                FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_tok_sess ON token_usage(session_key);
            CREATE INDEX IF NOT EXISTS idx_tok_room ON token_usage(room_id);
            """
        )
        await self._conn.commit()

    # ===== Rooms =====
    async def upsert_session(self, session_key: str) -> None:
        assert self._conn is not None
        async with self._lock:
            await self._conn.execute(
                """
                INSERT INTO sessions(session_key) VALUES(?)
                ON CONFLICT(session_key) DO UPDATE SET last_accessed=CURRENT_TIMESTAMP
                """,
                (session_key,),
            )
            await self._conn.commit()

    async def upsert_room(
        self, room_id: str, session_key: str, title: str, context_json: str | None
    ) -> None:
        assert self._conn is not None
        async with self._lock:
            await self.upsert_session(session_key)
            await self._conn.execute(
                """
                INSERT INTO rooms(room_id, session_key, title, context)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(room_id) DO UPDATE SET
                  session_key=excluded.session_key,
                  title=excluded.title,
                  context=excluded.context,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (room_id, session_key, title, context_json),
            )
            await self._conn.commit()

    async def list_rooms(self, session_key: str) -> list[dict[str, Any]]:
        assert self._conn is not None
        cur = await self._conn.execute(
            "SELECT room_id, title, context, created_at, updated_at FROM rooms WHERE session_key = ? ORDER BY updated_at DESC",
            (session_key,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def get_room(self, room_id: str) -> dict[str, Any] | None:
        assert self._conn is not None
        cur = await self._conn.execute(
            "SELECT room_id, session_key, title, context, created_at, updated_at FROM rooms WHERE room_id = ?",
            (room_id,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def delete_room(self, room_id: str) -> None:
        assert self._conn is not None
        async with self._lock:
            await self._conn.execute("DELETE FROM rooms WHERE room_id = ?", (room_id,))
            await self._conn.commit()

    # ===== Messages =====
    async def save_message(self, room_id: str, role: str, content: str) -> None:
        assert self._conn is not None
        async with self._lock:
            await self._conn.execute(
                "INSERT INTO messages(room_id, role, content) VALUES(?,?,?)",
                (room_id, role, content),
            )
            await self._conn.commit()

    async def list_messages(self, room_id: str, limit: int | None = None) -> list[dict[str, Any]]:
        assert self._conn is not None
        sql = "SELECT message_id, role, content, timestamp FROM messages WHERE room_id=? ORDER BY message_id ASC"
        params: Iterable[Any] = (room_id,)
        if limit:
            sql += " LIMIT ?"
            params = (room_id, limit)
        cur = await self._conn.execute(sql, params)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def list_messages_range(
        self, room_id: str, start: str | None = None, end: str | None = None
    ) -> list[dict[str, Any]]:
        """방 메시지 조회(날짜 범위 필터). start/end는 'YYYY-MM-DD HH:MM:SS' 문자열.

        SQLite의 TIMESTAMP 텍스트 비교 특성을 활용합니다.
        """
        assert self._conn is not None
        clauses = ["room_id = ?"]
        params: list[Any] = [room_id]
        if start:
            clauses.append("timestamp >= ?")
            params.append(start)
        if end:
            clauses.append("timestamp <= ?")
            params.append(end)
        where = " AND ".join(clauses)
        sql = f"SELECT message_id, role, content, timestamp FROM messages WHERE {where} ORDER BY message_id ASC"
        cur = await self._conn.execute(sql, params)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def list_token_usage_range(
        self, room_id: str, start: str | None = None, end: str | None = None
    ) -> list[dict[str, Any]]:
        """방별 토큰 사용량 조회(날짜 범위)."""
        assert self._conn is not None
        clauses = ["room_id = ?"]
        params: list[Any] = [room_id]
        if start:
            clauses.append("timestamp >= ?")
            params.append(start)
        if end:
            clauses.append("timestamp <= ?")
            params.append(end)
        where = " AND ".join(clauses)
        sql = f"SELECT usage_id, session_key, provider, token_info, timestamp FROM token_usage WHERE {where} ORDER BY usage_id ASC"
        cur = await self._conn.execute(sql, params)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def list_all_rooms(self) -> list[dict[str, Any]]:
        assert self._conn is not None
        cur = await self._conn.execute(
            "SELECT room_id, title, session_key, created_at, updated_at FROM rooms ORDER BY updated_at DESC"
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
