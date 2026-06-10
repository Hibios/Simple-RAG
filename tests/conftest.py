import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Literal

import aiosqlite
import pytest
from httpx import ASGITransport, AsyncClient

from src.core.database import get_db_session
from src.main import app

TEST_DB_PATH = "file:test_db?mode=memory&cache=shared"

@pytest.fixture(scope="session")
def anyio_backend() -> Literal["asyncio"]:
    return "asyncio"

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def init_test_database(anyio_backend: str) -> AsyncGenerator[None, None]:
    async with aiosqlite.connect(TEST_DB_PATH, uri=True) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                hash TEXT PRIMARY KEY,
                chunk TEXT,
                filename TEXT,
                embedding BLOB
            )
        """)
        await db.commit()
        yield

async def override_get_db_session() -> AsyncGenerator[aiosqlite.Connection, None]:
    async with aiosqlite.connect(TEST_DB_PATH, uri=True) as db:
        db.row_factory = aiosqlite.Row
        yield db

app.dependency_overrides[get_db_session] = override_get_db_session

@pytest.fixture
async def async_client(anyio_backend: str) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
