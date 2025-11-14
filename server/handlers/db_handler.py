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
        """스키마 버전 관리를 통한 마이그레이션"""
        assert self._conn is not None

        # 현재 DB 버전 확인
        cursor = await self._conn.execute("PRAGMA user_version")
        row = await cursor.fetchone()
        current_version = row[0] if row else 0

        # 버전 0: 초기 스키마 생성
        if current_version < 1:
            await self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_key TEXT PRIMARY KEY,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS rooms (
                    session_key TEXT NOT NULL,
                    room_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (session_key, room_id),
                    FOREIGN KEY (session_key) REFERENCES sessions(session_key) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_rooms_session ON rooms(session_key);

                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role in ('user','assistant')),
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_messages_room ON messages(room_id);
                CREATE INDEX IF NOT EXISTS idx_messages_ts ON messages(timestamp);

                CREATE TABLE IF NOT EXISTS token_usage (
                    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_key TEXT NOT NULL,
                    room_id TEXT,
                    provider TEXT NOT NULL,
                    token_info TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_tok_sess ON token_usage(session_key);
                CREATE INDEX IF NOT EXISTS idx_tok_room ON token_usage(room_id);

                PRAGMA user_version = 1;
                """
            )
            await self._conn.commit()

        # 버전 1→2: users 테이블 추가 (회원제 시스템)
        if current_version < 2:
            await self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

                PRAGMA user_version = 2;
                """
            )
            await self._conn.commit()

        # 버전 2→3: sessions 테이블에 user_id 외래키 추가
        if current_version < 3:
            await self._conn.executescript(
                """
                -- 임시 테이블 생성
                CREATE TABLE sessions_new (
                    session_key TEXT PRIMARY KEY,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );

                -- 기존 데이터 복사 (user_id는 NULL)
                INSERT INTO sessions_new (session_key, created_at, last_accessed)
                SELECT session_key, created_at, last_accessed FROM sessions;

                -- 기존 테이블 삭제 및 교체
                DROP TABLE sessions;
                ALTER TABLE sessions_new RENAME TO sessions;

                -- 인덱스 재생성
                CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

                PRAGMA user_version = 3;
                """
            )
            await self._conn.commit()

    # ===== Rooms =====
    async def _upsert_session_unlocked(self, session_key: str, user_id: int | None = None) -> None:
        """Lock 없이 세션 upsert (내부용)

        Args:
            session_key: 세션 키
            user_id: 사용자 ID (회원제 시스템용, None이면 비회원 세션)
        """
        assert self._conn is not None
        if user_id is not None:
            # user_id가 있으면 함께 저장/업데이트
            await self._conn.execute(
                """
                INSERT INTO sessions(session_key, user_id) VALUES(?, ?)
                ON CONFLICT(session_key) DO UPDATE SET
                    last_accessed=CURRENT_TIMESTAMP,
                    user_id=excluded.user_id
                """,
                (session_key, user_id),
            )
        else:
            # user_id 없으면 기존 방식 (last_accessed만 업데이트)
            await self._conn.execute(
                """
                INSERT INTO sessions(session_key) VALUES(?)
                ON CONFLICT(session_key) DO UPDATE SET last_accessed=CURRENT_TIMESTAMP
                """,
                (session_key,),
            )

    async def upsert_session(self, session_key: str, user_id: int | None = None) -> None:
        """세션 생성 또는 업데이트

        Args:
            session_key: 세션 키
            user_id: 사용자 ID (회원제 시스템용, None이면 비회원 세션)
        """
        assert self._conn is not None
        async with self._lock:
            await self._upsert_session_unlocked(session_key, user_id)
            await self._conn.commit()

    async def upsert_room(
        self,
        room_id: str,
        session_key: str,
        title: str,
        context_json: str | None,
        user_id: int | None = None,
    ) -> None:
        """방 생성 또는 업데이트

        Args:
            room_id: 방 ID
            session_key: 세션 키
            title: 방 제목
            context_json: 컨텍스트 JSON
            user_id: 사용자 ID (회원제 시스템용, None이면 비회원)
        """
        assert self._conn is not None
        async with self._lock:
            await self._upsert_session_unlocked(session_key, user_id)
            await self._conn.execute(
                """
                INSERT INTO rooms(session_key, room_id, title, context)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(session_key, room_id) DO UPDATE SET
                  title=excluded.title,
                  context=excluded.context,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (session_key, room_id, title, context_json),
            )
            await self._conn.commit()

    async def list_rooms(self, session_key: str) -> list[dict[str, Any]]:
        """세션 키로 방 목록 조회"""
        assert self._conn is not None
        cur = await self._conn.execute(
            "SELECT room_id, title, context, created_at, updated_at FROM rooms WHERE session_key = ? ORDER BY updated_at DESC",
            (session_key,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def list_rooms_by_user_id(self, user_id: int) -> list[dict[str, Any]]:
        """user_id로 방 목록 조회 (세션 JOIN)

        Args:
            user_id: 사용자 ID

        Returns:
            방 목록 (room_id, title, context, created_at, updated_at, session_key)
        """
        assert self._conn is not None
        cur = await self._conn.execute(
            """
            SELECT r.room_id, r.title, r.context, r.created_at, r.updated_at, r.session_key
            FROM rooms r
            JOIN sessions s ON r.session_key = s.session_key
            WHERE s.user_id = ?
            ORDER BY r.updated_at DESC
            """,
            (user_id,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def get_room(self, room_id: str, session_key: str | None = None) -> dict[str, Any] | None:
        """방 조회 (세션 키로 격리)

        Args:
            room_id: 방 ID
            session_key: 세션 키 (None이면 세션 체크 안 함 - 하위 호환용, 보안상 권장하지 않음)
        """
        assert self._conn is not None
        if session_key is not None:
            # 세션 키로 격리 (권장)
            cur = await self._conn.execute(
                "SELECT room_id, session_key, title, context, created_at, updated_at FROM rooms WHERE room_id = ? AND session_key = ?",
                (room_id, session_key),
            )
        else:
            # 하위 호환용 (보안 취약)
            cur = await self._conn.execute(
                "SELECT room_id, session_key, title, context, created_at, updated_at FROM rooms WHERE room_id = ?",
                (room_id,),
            )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def delete_room(self, room_id: str, session_key: str | None = None) -> None:
        """방 삭제 (세션 키로 격리)

        Args:
            room_id: 방 ID
            session_key: 세션 키 (None이면 세션 체크 안 함 - 하위 호환용, 보안상 권장하지 않음)

        Note:
            메시지와 토큰 사용량도 함께 삭제됩니다 (CASCADE 대체)
        """
        assert self._conn is not None
        async with self._lock:
            # 관련 메시지 먼저 삭제
            await self._conn.execute("DELETE FROM messages WHERE room_id = ?", (room_id,))

            # 관련 토큰 사용량 삭제
            await self._conn.execute("DELETE FROM token_usage WHERE room_id = ?", (room_id,))

            # 방 삭제
            if session_key is not None:
                # 세션 키로 격리 (권장)
                await self._conn.execute(
                    "DELETE FROM rooms WHERE room_id = ? AND session_key = ?",
                    (room_id, session_key),
                )
            else:
                # 하위 호환용 (보안 취약)
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

    async def save_token_usage(
        self,
        session_key: str,
        room_id: str,
        provider: str,
        token_info: dict | str | None,
    ) -> None:
        """토큰 사용량 저장.

        token_info는 dict 또는 JSON 문자열 허용. None이면 저장하지 않음.
        """
        if token_info is None:
            return
        assert self._conn is not None
        import json as _json

        info_str = (
            _json.dumps(token_info, ensure_ascii=False)
            if isinstance(token_info, dict)
            else str(token_info)
        )
        async with self._lock:
            await self._conn.execute(
                """
                INSERT INTO token_usage(session_key, room_id, provider, token_info)
                VALUES(?, ?, ?, ?)
                """,
                (session_key, room_id, provider, info_str),
            )
            await self._conn.commit()

    async def list_all_rooms(self) -> list[dict[str, Any]]:
        assert self._conn is not None
        cur = await self._conn.execute(
            "SELECT room_id, title, session_key, created_at, updated_at FROM rooms ORDER BY updated_at DESC"
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    # ===== Users =====
    async def create_user(self, username: str, email: str, password_hash: str) -> int | None:
        """사용자 생성

        Returns:
            user_id: 생성된 사용자 ID
            None: 중복 사용자명/이메일로 실패
        """
        assert self._conn is not None
        async with self._lock:
            try:
                cursor = await self._conn.execute(
                    """
                    INSERT INTO users(username, email, password_hash)
                    VALUES(?, ?, ?)
                    """,
                    (username, email, password_hash),
                )
                await self._conn.commit()
                return cursor.lastrowid
            except Exception:
                # UNIQUE constraint 위반 (중복 username 또는 email)
                return None

    async def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        """사용자명으로 사용자 조회"""
        assert self._conn is not None
        cursor = await self._conn.execute(
            """
            SELECT user_id, username, email, password_hash, created_at, last_login
            FROM users
            WHERE username = ?
            """,
            (username,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """이메일로 사용자 조회"""
        assert self._conn is not None
        cursor = await self._conn.execute(
            """
            SELECT user_id, username, email, password_hash, created_at, last_login
            FROM users
            WHERE email = ?
            """,
            (email,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        """user_id로 사용자 조회"""
        assert self._conn is not None
        cursor = await self._conn.execute(
            """
            SELECT user_id, username, email, password_hash, created_at, last_login
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def update_last_login(self, user_id: int) -> None:
        """마지막 로그인 시간 업데이트"""
        assert self._conn is not None
        async with self._lock:
            await self._conn.execute(
                """
                UPDATE users
                SET last_login = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (user_id,),
            )
            await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
