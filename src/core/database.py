import collections.abc
from pathlib import Path

import aiosqlite

from core import settings

DB_PATH: Path = Path(settings.DATABASE_URL)


async def get_db_session() -> collections.abc.AsyncGenerator[
    aiosqlite.Connection, None
]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                hash TEXT PRIMARY KEY,
                chunk TEXT,
                filename TEXT,
                embedding BLOB
            )
        """)
        await db.execute("PRAGMA journal_mode = WAL")
        await db.execute("PRAGMA synchronous = NORMAL")
        await db.commit()
