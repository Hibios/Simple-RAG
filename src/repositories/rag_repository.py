from collections import abc

import aiosqlite


class RAGRepository:
    def __init__(self, db: aiosqlite.Connection) -> None:
        self.db: aiosqlite.Connection = db

    async def get_existing_hashes(self) -> set[str]:
        async with self.db.execute("SELECT hash FROM cache") as cursor:
            rows = await cursor.fetchall()
            return {row["hash"] for row in rows}

    async def save_embeddings_batch(
        self, batch_data: list[tuple[str, str, str, bytes]]
    ) -> None:
        await self.db.executemany(
            """INSERT OR IGNORE INTO cache (hash, chunk, filename, embedding) 
               VALUES (?, ?, ?, ?)""",
            batch_data,
        )
        await self.db.commit()

    async def get_all_embeddings(self) -> abc.Iterable[aiosqlite.Row]:
        async with self.db.execute("SELECT chunk, embedding FROM cache") as cursor:
            return await cursor.fetchall()
