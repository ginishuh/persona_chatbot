import asyncio
import logging
import os
import shutil
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)


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
        """DB 버전 관리 및 마이그레이션 시스템 (user_id 기반)."""
        assert self._conn is not None

        # 현재 DB 버전 확인
        cur = await self._conn.execute("PRAGMA user_version")
        row = await cur.fetchone()
        current_version = row[0] if row else 0

        # 최신 버전: v4 (user_id 기반 재설계)
        TARGET_VERSION = 4

        if current_version == 0:
            # 새 DB: v4 스키마로 바로 생성
            await self._conn.executescript(
                """
                -- users 테이블
                CREATE TABLE users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_approved INTEGER DEFAULT 0,
                    role TEXT DEFAULT 'user',
                    approved_by INTEGER,
                    approved_at TIMESTAMP
                );

                -- rooms 테이블 (user_id 기반)
                CREATE TABLE rooms (
                    user_id INTEGER NOT NULL,
                    room_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, room_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
                CREATE INDEX idx_rooms_user ON rooms(user_id);
                CREATE INDEX idx_rooms_updated ON rooms(updated_at);

                -- messages 테이블 (user_id 기반)
                CREATE TABLE messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    room_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role in ('user','assistant')),
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id, room_id) REFERENCES rooms(user_id, room_id) ON DELETE CASCADE
                );
                CREATE INDEX idx_messages_room ON messages(user_id, room_id);
                CREATE INDEX idx_messages_ts ON messages(timestamp);

                -- token_usage 테이블 (user_id 기반)
                CREATE TABLE token_usage (
                    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    room_id TEXT,
                    provider TEXT NOT NULL,
                    token_info TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
                CREATE INDEX idx_tok_user ON token_usage(user_id);
                CREATE INDEX idx_tok_room ON token_usage(room_id);
                """
            )
            await self._conn.commit()
            current_version = 4
        elif current_version < 4:
            # 구버전 DB: v4로 마이그레이션 (기존 데이터 버림)
            await self._maybe_backup_legacy_db()
            await self._migrate_to_v4()
            # v4 마이그레이션 후 v3의 승인 컬럼 추가 (users 테이블에만)
            await self._migrate_to_v3()
            current_version = 4

        # 버전 업데이트
        if current_version == TARGET_VERSION:
            await self._conn.execute(f"PRAGMA user_version = {TARGET_VERSION}")
            await self._conn.commit()

    async def _maybe_backup_legacy_db(self) -> None:
        """구버전 DB를 파괴하기 전에 백업 파일을 생성."""
        db_file = Path(self.db_path)
        if not db_file.exists():
            return

        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_name = f"{db_file.name}.legacy-{timestamp}.bak"
        backup_path = db_file.with_name(backup_name)

        try:
            # SQLite WAL 모드일 수 있으므로 본파일과 부가 파일들을 같이 복사
            shutil.copy2(db_file, backup_path)
            for suffix in ("-wal", "-shm"):
                aux = db_file.with_name(db_file.name + suffix)
                if aux.exists():
                    shutil.copy2(aux, backup_path.with_name(backup_name + suffix))
            logger.warning("Legacy DB backup created at %s", backup_path)
        except Exception:
            logger.exception("Failed to create legacy DB backup before migration")

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

    async def _migrate_to_v3(self) -> None:
        """v2 → v3: users 테이블에 승인 및 역할 관리 추가"""
        assert self._conn is not None

        # 기존 테이블 구조 확인
        cur = await self._conn.execute("PRAGMA table_info(users)")
        columns = await cur.fetchall()
        column_names = [col[1] for col in columns]

        # is_approved 컬럼이 없으면 추가
        if "is_approved" not in column_names:
            await self._conn.execute("ALTER TABLE users ADD COLUMN is_approved INTEGER DEFAULT 0")

        # role 컬럼이 없으면 추가
        if "role" not in column_names:
            await self._conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")

        # approved_by 컬럼이 없으면 추가 (어떤 관리자가 승인했는지 기록)
        if "approved_by" not in column_names:
            await self._conn.execute("ALTER TABLE users ADD COLUMN approved_by INTEGER")

        # approved_at 컬럼이 없으면 추가
        if "approved_at" not in column_names:
            await self._conn.execute("ALTER TABLE users ADD COLUMN approved_at TIMESTAMP")

        await self._conn.commit()

    async def _migrate_to_v4(self) -> None:
        """v3 → v4: user_id 기반 재설계 (기존 데이터 삭제)."""
        assert self._conn is not None

        # 외래 키 제약 조건 비활성화 (테이블 삭제 시 오류 방지)
        await self._conn.execute("PRAGMA foreign_keys = OFF")

        # 기존 테이블 모두 삭제
        await self._conn.execute("DROP TABLE IF EXISTS messages")
        await self._conn.execute("DROP TABLE IF EXISTS rooms")
        await self._conn.execute("DROP TABLE IF EXISTS sessions")
        await self._conn.execute("DROP TABLE IF EXISTS token_usage")

        # users 테이블은 유지 (이미 존재)

        # 새 스키마로 테이블 생성
        await self._conn.executescript(
            """
            -- rooms 테이블 (user_id 기반)
            CREATE TABLE rooms (
                user_id INTEGER NOT NULL,
                room_id TEXT NOT NULL,
                title TEXT NOT NULL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, room_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            CREATE INDEX idx_rooms_user ON rooms(user_id);
            CREATE INDEX idx_rooms_updated ON rooms(updated_at);

            -- messages 테이블 (user_id 기반)
            CREATE TABLE messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                room_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role in ('user','assistant')),
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id, room_id) REFERENCES rooms(user_id, room_id) ON DELETE CASCADE
            );
            CREATE INDEX idx_messages_room ON messages(user_id, room_id);
            CREATE INDEX idx_messages_ts ON messages(timestamp);

            -- token_usage 테이블 (user_id 기반)
            CREATE TABLE token_usage (
                usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                room_id TEXT,
                provider TEXT NOT NULL,
                token_info TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            CREATE INDEX idx_tok_user ON token_usage(user_id);
            CREATE INDEX idx_tok_room ON token_usage(room_id);
            """
        )

        # 외래 키 제약 조건 다시 활성화
        await self._conn.execute("PRAGMA foreign_keys = ON")

        await self._conn.commit()

    # ===== Rooms =====
    async def upsert_room(
        self,
        room_id: str,
        user_id: int,
        title: str,
        context_json: str | None,
    ) -> None:
        """방 생성 또는 업데이트 (user_id 기반)

        Args:
            room_id: 방 ID
            user_id: 사용자 ID
            title: 방 제목
            context_json: 컨텍스트 JSON
        """
        assert self._conn is not None
        async with self._lock:
            await self._conn.execute(
                """
                INSERT INTO rooms(user_id, room_id, title, context)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(user_id, room_id) DO UPDATE SET
                  title=excluded.title,
                  context=excluded.context,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (user_id, room_id, title, context_json),
            )
            await self._conn.commit()

    async def list_rooms(self, user_id: int) -> list[dict[str, Any]]:
        """채팅방 목록 조회 (user_id 기반)

        Args:
            user_id: 사용자 ID

        Returns:
            방 목록 (user_id, room_id, title, context, created_at, updated_at)
        """
        assert self._conn is not None
        cur = await self._conn.execute(
            """
            SELECT user_id, room_id, title, context, created_at, updated_at
            FROM rooms
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def get_room(self, room_id: str, user_id: int) -> dict[str, Any] | None:
        """방 조회 (user_id 기반)

        Args:
            room_id: 방 ID
            user_id: 사용자 ID
        """
        assert self._conn is not None
        cur = await self._conn.execute(
            "SELECT user_id, room_id, title, context, created_at, updated_at FROM rooms WHERE room_id = ? AND user_id = ?",
            (room_id, user_id),
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def delete_room(self, room_id: str, user_id: int) -> None:
        """방 삭제 (user_id 기반)

        Args:
            room_id: 방 ID
            user_id: 사용자 ID

        Note:
            메시지와 토큰 사용량은 FOREIGN KEY CASCADE로 자동 삭제됩니다
        """
        assert self._conn is not None
        async with self._lock:
            # 방 삭제 (CASCADE로 메시지와 토큰 사용량 자동 삭제)
            await self._conn.execute(
                "DELETE FROM rooms WHERE room_id = ? AND user_id = ?",
                (room_id, user_id),
            )
            await self._conn.commit()

    # ===== Messages =====
    async def save_message(self, room_id: str, role: str, content: str, user_id: int) -> None:
        """메시지 저장 (user_id 기반)

        Args:
            room_id: 방 ID
            role: 'user' 또는 'assistant'
            content: 메시지 내용
            user_id: 사용자 ID
        """
        assert self._conn is not None
        async with self._lock:
            await self._conn.execute(
                "INSERT INTO messages(user_id, room_id, role, content) VALUES(?,?,?,?)",
                (user_id, room_id, role, content),
            )
            await self._conn.commit()

    async def list_messages(
        self, room_id: str, user_id: int, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """메시지 조회 (user_id 기반)

        Args:
            room_id: 방 ID
            user_id: 사용자 ID
            limit: 최대 조회 개수
        """
        assert self._conn is not None
        sql = "SELECT message_id, role, content, timestamp FROM messages WHERE room_id=? AND user_id=? ORDER BY message_id ASC"
        params: Iterable[Any] = (room_id, user_id)
        if limit:
            sql += " LIMIT ?"
            params = (room_id, user_id, limit)
        cur = await self._conn.execute(sql, params)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def list_messages_range(
        self,
        room_id: str,
        user_id: int,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict[str, Any]]:
        """방 메시지 조회 (날짜 범위 필터, user_id 기반)

        Args:
            room_id: 방 ID
            user_id: 사용자 ID
            start: 시작 시간 'YYYY-MM-DD HH:MM:SS'
            end: 종료 시간 'YYYY-MM-DD HH:MM:SS'
        """
        assert self._conn is not None
        clauses = ["room_id = ?", "user_id = ?"]
        params: list[Any] = [room_id, user_id]

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
        user_id: int,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict[str, Any]]:
        """방별 토큰 사용량 조회 (날짜 범위, user_id 기반)

        Args:
            room_id: 방 ID
            user_id: 사용자 ID
            start: 시작 시간
            end: 종료 시간
        """
        assert self._conn is not None
        clauses = ["room_id = ?", "user_id = ?"]
        params: list[Any] = [room_id, user_id]

        if start:
            clauses.append("timestamp >= ?")
            params.append(start)
        if end:
            clauses.append("timestamp <= ?")
            params.append(end)
        where = " AND ".join(clauses)
        sql = f"SELECT usage_id, user_id, provider, token_info, timestamp FROM token_usage WHERE {where} ORDER BY usage_id ASC"
        cur = await self._conn.execute(sql, params)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def save_token_usage(
        self,
        user_id: int,
        room_id: str,
        provider: str,
        token_info: dict | str | None,
    ) -> None:
        """토큰 사용량 저장 (user_id 기반)

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
                INSERT INTO token_usage(user_id, room_id, provider, token_info)
                VALUES(?, ?, ?, ?)
                """,
                (user_id, room_id, provider, info_str),
            )
            await self._conn.commit()

    async def list_all_rooms(self) -> list[dict[str, Any]]:
        """모든 방 목록 조회 (관리자용)"""
        assert self._conn is not None
        cur = await self._conn.execute(
            "SELECT user_id, room_id, title, created_at, updated_at FROM rooms ORDER BY updated_at DESC"
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
        """사용자명으로 조회"""
        assert self._conn is not None
        cur = await self._conn.execute(
            """
            SELECT user_id, username, password_hash, email, created_at, last_login,
                   is_approved, role, approved_by, approved_at
            FROM users WHERE username = ?
            """,
            (username,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        """사용자 ID로 조회"""
        assert self._conn is not None
        cur = await self._conn.execute(
            """
            SELECT user_id, username, password_hash, email, created_at, last_login,
                   is_approved, role, approved_by, approved_at
            FROM users WHERE user_id = ?
            """,
            (user_id,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def update_user_last_login(self, user_id: int) -> None:
        """사용자 마지막 로그인 시간 갱신"""
        assert self._conn is not None
        await self._conn.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,)
        )
        await self._conn.commit()

    async def list_users(self) -> list[dict[str, Any]]:
        """모든 사용자 조회"""
        assert self._conn is not None
        cur = await self._conn.execute(
            """
            SELECT user_id, username, email, created_at, last_login,
                   is_approved, role, approved_by, approved_at
            FROM users ORDER BY created_at DESC
            """
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def list_pending_users(self) -> list[dict[str, Any]]:
        """승인 대기 중인 사용자 조회"""
        assert self._conn is not None
        cur = await self._conn.execute(
            """
            SELECT user_id, username, email, created_at
            FROM users
            WHERE is_approved = 0
            ORDER BY created_at ASC
            """
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def approve_user(self, user_id: int, admin_user_id: int) -> bool:
        """사용자 승인

        Args:
            user_id: 승인할 사용자 ID
            admin_user_id: 승인하는 관리자 ID

        Returns:
            성공 여부
        """
        assert self._conn is not None
        try:
            await self._conn.execute(
                """
                UPDATE users
                SET is_approved = 1,
                    approved_by = ?,
                    approved_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (admin_user_id, user_id),
            )
            await self._conn.commit()
            return True
        except Exception:
            return False

    async def create_admin_user(self, username: str, email: str, password_hash: str) -> int | None:
        """관리자 사용자 생성 (즉시 승인 + role='admin')

        Returns:
            user_id: 생성된 관리자 ID
            None: 중복 사용자명/이메일로 실패
        """
        assert self._conn is not None
        async with self._lock:
            try:
                cursor = await self._conn.execute(
                    """
                    INSERT INTO users(username, email, password_hash, is_approved, role)
                    VALUES(?, ?, ?, 1, 'admin')
                    """,
                    (username, email, password_hash),
                )
                await self._conn.commit()
                return cursor.lastrowid
            except Exception:
                # UNIQUE constraint 위반
                return None

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
