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
        """DB 버전 관리 및 마이그레이션 시스템."""
        assert self._conn is not None

        # 현재 DB 버전 확인
        cur = await self._conn.execute("PRAGMA user_version")
        row = await cur.fetchone()
        current_version = row[0] if row else 0

        # 최신 버전
        TARGET_VERSION = 2

        if current_version == 0:
            # 테이블 존재 여부 확인 (새 DB vs 구버전 DB 구분)
            cur = await self._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='rooms'"
            )
            row = await cur.fetchone()
            is_new_db = row is None

            if is_new_db:
                # 새 DB: v1 스키마로 바로 생성
                await self._conn.executescript(
                    """
                    CREATE TABLE sessions (
                        session_key TEXT PRIMARY KEY,
                        user_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE rooms (
                        session_key TEXT NOT NULL,
                        room_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        context TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (session_key, room_id),
                        FOREIGN KEY (session_key) REFERENCES sessions(session_key) ON DELETE CASCADE
                    );
                    CREATE INDEX idx_rooms_session ON rooms(session_key);

                    CREATE TABLE messages (
                        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_key TEXT NOT NULL,
                        room_id TEXT NOT NULL,
                        role TEXT NOT NULL CHECK(role in ('user','assistant')),
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX idx_messages_room_session ON messages(room_id, session_key);
                    CREATE INDEX idx_messages_ts ON messages(timestamp);

                    CREATE TABLE token_usage (
                        usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_key TEXT NOT NULL,
                        room_id TEXT,
                        provider TEXT NOT NULL,
                        token_info TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX idx_tok_sess ON token_usage(session_key);
                    CREATE INDEX idx_tok_room ON token_usage(room_id);
                    """
                )
                await self._conn.commit()
                current_version = 1
            else:
                # 구버전 DB: 마이그레이션 필요
                await self._migrate_to_v1()
                current_version = 1

        # v1 → v2: users 테이블 추가
        if current_version < 2:
            await self._migrate_to_v2()
            current_version = 2

        # 버전 업데이트
        if current_version == TARGET_VERSION:
            await self._conn.execute(f"PRAGMA user_version = {TARGET_VERSION}")
            await self._conn.commit()

    async def _migrate_to_v1(self) -> None:
        """v0 → v1: rooms와 messages 테이블에 복합 PK 및 세션 격리 구현."""
        assert self._conn is not None

        # Step 1: rooms 테이블 복합 PK로 재구성 확인
        # 기존 rooms 테이블의 PK 구조 확인
        cur = await self._conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='rooms'"
        )
        row = await cur.fetchone()
        needs_rooms_migration = False

        if row:
            table_sql = row[0]
            # 복합 PK가 없으면 마이그레이션 필요
            if "PRIMARY KEY (session_key, room_id)" not in table_sql:
                needs_rooms_migration = True

        if needs_rooms_migration:
            # rooms 테이블 재구성
            # 1. 기존 테이블 컬럼 확인
            cur = await self._conn.execute("PRAGMA table_info(rooms)")
            columns = await cur.fetchall()
            column_names = [col[1] for col in columns]

            # 2. 기존 session_key 값 확인 및 sessions 테이블에 추가
            has_session_key = "session_key" in column_names
            if has_session_key:
                # 기존 session_key 값들을 sessions 테이블에 추가 (FK 만족)
                cur = await self._conn.execute(
                    "SELECT DISTINCT session_key FROM rooms WHERE session_key IS NOT NULL"
                )
                existing_keys = await cur.fetchall()
                for (key,) in existing_keys:
                    if key:  # NULL이 아닌 경우만
                        await self._conn.execute(
                            "INSERT OR IGNORE INTO sessions(session_key) VALUES(?)", (key,)
                        )
            # session_key가 없거나 NULL인 경우를 위해 'legacy' 세션도 추가
            await self._conn.execute("INSERT OR IGNORE INTO sessions(session_key) VALUES('legacy')")

            # 3. 기존 테이블 백업
            await self._conn.execute("ALTER TABLE rooms RENAME TO rooms_old")

            # 4. 새 rooms 테이블 생성 (복합 PK)
            await self._conn.execute(
                """
                CREATE TABLE rooms (
                    session_key TEXT NOT NULL,
                    room_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (session_key, room_id),
                    FOREIGN KEY (session_key) REFERENCES sessions(session_key) ON DELETE CASCADE
                )
                """
            )

            # 5. 기존 데이터 복사 (컬럼 존재 여부에 따라 동적 쿼리 생성)
            # session_key: 기존 컬럼이 있으면 유지, 없거나 NULL이면 'legacy' 사용
            if has_session_key:
                select_parts = ["COALESCE(session_key, 'legacy') as session_key", "room_id"]
            else:
                select_parts = ["'legacy' as session_key", "room_id"]

            # title 컬럼
            if "title" in column_names:
                select_parts.append("title")
            else:
                select_parts.append("room_id as title")  # title이 없으면 room_id 사용

            # context 컬럼
            if "context" in column_names:
                select_parts.append("context")
            else:
                select_parts.append("NULL as context")

            # created_at 컬럼
            if "created_at" in column_names:
                select_parts.append("created_at")
            else:
                select_parts.append("CURRENT_TIMESTAMP as created_at")

            # updated_at 컬럼
            if "updated_at" in column_names:
                select_parts.append("updated_at")
            else:
                select_parts.append("CURRENT_TIMESTAMP as updated_at")

            select_clause = ", ".join(select_parts)
            await self._conn.execute(
                f"INSERT INTO rooms (session_key, room_id, title, context, created_at, updated_at) "
                f"SELECT {select_clause} FROM rooms_old"
            )

            # 6. 기존 테이블 삭제
            await self._conn.execute("DROP TABLE rooms_old")

            # 7. 인덱스 재생성
            await self._conn.execute("CREATE INDEX idx_rooms_session ON rooms(session_key)")

        # Step 2: messages 테이블에 session_key 추가
        cur = await self._conn.execute("PRAGMA table_info(messages)")
        columns = await cur.fetchall()
        column_names = [col[1] for col in columns]

        if "session_key" not in column_names:
            # 1. 새 messages 테이블 생성 (session_key 포함)
            await self._conn.execute(
                """
                CREATE TABLE messages_new (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_key TEXT NOT NULL,
                    room_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role in ('user','assistant')),
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # 2. 기존 데이터 복사 (rooms와 조인하여 session_key 가져오기)
            # 고아 메시지(room이 없는)는 'legacy' session_key로 이동

            # 기존 messages 테이블 컬럼 확인
            cur = await self._conn.execute("PRAGMA table_info(messages)")
            msg_columns = await cur.fetchall()
            msg_column_names = [col[1] for col in msg_columns]

            # timestamp 컬럼이 있으면 사용, 없으면 CURRENT_TIMESTAMP 사용
            timestamp_expr = (
                "m.timestamp" if "timestamp" in msg_column_names else "CURRENT_TIMESTAMP"
            )

            await self._conn.execute(
                f"""
                INSERT INTO messages_new (message_id, session_key, room_id, role, content, timestamp)
                SELECT
                    m.message_id,
                    COALESCE(r.session_key, 'legacy') as session_key,
                    m.room_id,
                    m.role,
                    m.content,
                    {timestamp_expr}
                FROM messages m
                LEFT JOIN rooms r ON m.room_id = r.room_id
                """
            )

            # 3. 기존 테이블 삭제 및 새 테이블로 교체
            await self._conn.execute("DROP TABLE messages")
            await self._conn.execute("ALTER TABLE messages_new RENAME TO messages")

            # 4. 인덱스 재생성
            await self._conn.execute(
                "CREATE INDEX idx_messages_room_session ON messages(room_id, session_key)"
            )
            await self._conn.execute("CREATE INDEX idx_messages_ts ON messages(timestamp)")

        await self._conn.commit()

    async def _migrate_to_v2(self) -> None:
        """v1 → v2: users 테이블 추가 (회원제 시스템)"""
        assert self._conn is not None

        # users 테이블 생성 (PR #18 스키마)
        await self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
            """
        )

        # 인덱스 생성
        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

        await self._conn.commit()

    # ===== Rooms =====
    async def _upsert_session_unlocked(self, session_key: str) -> None:
        """Lock 없이 세션 upsert (내부용)"""
        assert self._conn is not None
        await self._conn.execute(
            """
            INSERT INTO sessions(session_key) VALUES(?)
            ON CONFLICT(session_key) DO UPDATE SET last_accessed=CURRENT_TIMESTAMP
            """,
            (session_key,),
        )

    async def upsert_session(self, session_key: str) -> None:
        assert self._conn is not None
        async with self._lock:
            await self._upsert_session_unlocked(session_key)
            await self._conn.commit()

    async def upsert_room(
        self, room_id: str, session_key: str, title: str, context_json: str | None
    ) -> None:
        assert self._conn is not None
        async with self._lock:
            await self._upsert_session_unlocked(session_key)
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
        assert self._conn is not None
        cur = await self._conn.execute(
            "SELECT room_id, title, context, created_at, updated_at FROM rooms WHERE session_key = ? ORDER BY updated_at DESC",
            (session_key,),
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
            if session_key is not None:
                # 세션 키로 격리하여 삭제 (권장)
                # 관련 메시지 먼저 삭제
                await self._conn.execute(
                    "DELETE FROM messages WHERE room_id = ? AND session_key = ?",
                    (room_id, session_key),
                )

                # 관련 토큰 사용량 삭제
                await self._conn.execute(
                    "DELETE FROM token_usage WHERE room_id = ? AND session_key = ?",
                    (room_id, session_key),
                )

                # 방 삭제
                await self._conn.execute(
                    "DELETE FROM rooms WHERE room_id = ? AND session_key = ?",
                    (room_id, session_key),
                )
            else:
                # 하위 호환용 (보안 취약 - 모든 세션의 데이터 삭제)
                await self._conn.execute("DELETE FROM messages WHERE room_id = ?", (room_id,))
                await self._conn.execute("DELETE FROM token_usage WHERE room_id = ?", (room_id,))
                await self._conn.execute("DELETE FROM rooms WHERE room_id = ?", (room_id,))

            await self._conn.commit()

    # ===== Messages =====
    async def save_message(self, room_id: str, role: str, content: str, session_key: str) -> None:
        """메시지 저장 (세션 키로 격리)

        Args:
            room_id: 방 ID
            role: 'user' 또는 'assistant'
            content: 메시지 내용
            session_key: 세션 키
        """
        assert self._conn is not None
        async with self._lock:
            await self._conn.execute(
                "INSERT INTO messages(session_key, room_id, role, content) VALUES(?,?,?,?)",
                (session_key, room_id, role, content),
            )
            await self._conn.commit()

    async def list_messages(
        self, room_id: str, session_key: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """메시지 조회 (세션 키로 격리)

        Args:
            room_id: 방 ID
            session_key: 세션 키 (None이면 세션 체크 안 함 - 하위 호환용, 보안상 권장하지 않음)
            limit: 최대 조회 개수
        """
        assert self._conn is not None
        if session_key is not None:
            # 세션 키로 격리 (권장)
            sql = "SELECT message_id, role, content, timestamp FROM messages WHERE room_id=? AND session_key=? ORDER BY message_id ASC"
            params: Iterable[Any] = (room_id, session_key)
            if limit:
                sql += " LIMIT ?"
                params = (room_id, session_key, limit)
        else:
            # 하위 호환용 (보안 취약)
            sql = "SELECT message_id, role, content, timestamp FROM messages WHERE room_id=? ORDER BY message_id ASC"
            params = (room_id,)
            if limit:
                sql += " LIMIT ?"
                params = (room_id, limit)
        cur = await self._conn.execute(sql, params)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def list_messages_range(
        self,
        room_id: str,
        session_key: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict[str, Any]]:
        """방 메시지 조회(날짜 범위 필터, 세션 키로 격리).

        Args:
            room_id: 방 ID
            session_key: 세션 키 (None이면 세션 체크 안 함 - 하위 호환용, 보안상 권장하지 않음)
            start: 시작 시간 'YYYY-MM-DD HH:MM:SS'
            end: 종료 시간 'YYYY-MM-DD HH:MM:SS'

        SQLite의 TIMESTAMP 텍스트 비교 특성을 활용합니다.
        """
        assert self._conn is not None
        clauses = ["room_id = ?"]
        params: list[Any] = [room_id]

        if session_key is not None:
            # 세션 키로 격리 (권장)
            clauses.append("session_key = ?")
            params.append(session_key)

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
        self,
        room_id: str,
        session_key: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict[str, Any]]:
        """방별 토큰 사용량 조회(날짜 범위, 세션 키로 격리).

        Args:
            room_id: 방 ID
            session_key: 세션 키 (None이면 세션 체크 안 함 - 하위 호환용, 보안상 권장하지 않음)
            start: 시작 시간
            end: 종료 시간
        """
        assert self._conn is not None
        clauses = ["room_id = ?"]
        params: list[Any] = [room_id]

        if session_key is not None:
            # 세션 키로 격리 (권장)
            clauses.append("session_key = ?")
            params.append(session_key)

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
    async def create_user(self, username: str, password_hash: str, email: str = None) -> int:
        """사용자 생성 (회원가입 또는 seed)"""
        assert self._conn is not None
        cur = await self._conn.execute(
            "INSERT INTO users(username, password_hash, email) VALUES(?, ?, ?)",
            (username, password_hash, email),
        )
        await self._conn.commit()
        return cur.lastrowid

    async def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        """사용자명으로 조회"""
        assert self._conn is not None
        cur = await self._conn.execute(
            "SELECT user_id, username, password_hash, email, is_active, created_at FROM users WHERE username = ?",
            (username,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        """사용자 ID로 조회"""
        assert self._conn is not None
        cur = await self._conn.execute(
            "SELECT user_id, username, password_hash, email, is_active, created_at FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def update_user_active(self, user_id: int, is_active: bool) -> None:
        """사용자 활성화/비활성화"""
        assert self._conn is not None
        await self._conn.execute(
            "UPDATE users SET is_active = ? WHERE user_id = ?", (is_active, user_id)
        )
        await self._conn.commit()

    async def list_users(self) -> list[dict[str, Any]]:
        """모든 사용자 조회"""
        assert self._conn is not None
        cur = await self._conn.execute(
            "SELECT user_id, username, email, is_active, created_at FROM users ORDER BY created_at DESC"
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
