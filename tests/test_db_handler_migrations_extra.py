import aiosqlite
import pytest

from server.handlers.db_handler import DBHandler


@pytest.mark.asyncio
async def test_migrate_to_v4_creates_tables(tmp_path):
    db_path = str(tmp_path / "migrate_v4.db")
    db = DBHandler(db_path)

    # create a raw connection and assign
    conn = await aiosqlite.connect(db_path)
    db._conn = conn

    # call migrate to v4
    await db._migrate_to_v4()

    # check that tables exist
    cur = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    rows = await cur.fetchall()
    names = {r[0] for r in rows}
    assert "rooms" in names
    assert "messages" in names
    assert "token_usage" in names

    await conn.close()


@pytest.mark.asyncio
async def test_migrate_to_v2_and_v3_users_columns(tmp_path):
    db_path = str(tmp_path / "migrate_v23.db")
    db = DBHandler(db_path)

    conn = await aiosqlite.connect(db_path)
    db._conn = conn

    # run v2 migration (creates users table)
    await db._migrate_to_v2()

    cur = await conn.execute("PRAGMA table_info(users)")
    cols = await cur.fetchall()
    col_names = [c[1] for c in cols]
    assert "username" in col_names

    # run v3 migration which should add approval/role columns
    await db._migrate_to_v3()
    cur2 = await conn.execute("PRAGMA table_info(users)")
    cols2 = await cur2.fetchall()
    col_names2 = [c[1] for c in cols2]
    assert "is_approved" in col_names2
    assert "role" in col_names2
    assert "approved_by" in col_names2
    assert "approved_at" in col_names2

    await conn.close()


def touch(path):
    with open(path, "w") as f:
        f.write("x")


@pytest.mark.asyncio
async def test_maybe_backup_legacy_db_creates_backup(tmp_path):
    db_file = tmp_path / "legacy.db"
    db_file.parent.mkdir(parents=True, exist_ok=True)
    # create main and WAL file
    touch(db_file)
    touch(db_file.with_name(db_file.name + "-wal"))

    db = DBHandler(str(db_file))

    # call backup function
    await db._maybe_backup_legacy_db()

    # find backup files
    backups = list(tmp_path.glob("*.legacy-*.bak"))
    assert backups, "expected a legacy backup file to be created"
