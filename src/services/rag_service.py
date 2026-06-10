import asyncio
import hashlib
from collections import abc

import numpy as np
from fastapi import UploadFile

from core.config import settings
from core.openai_client import openai_client
from repositories.rag_repository import RAGRepository


class RAGService:
    def __init__(self, repository: RAGRepository) -> None:
        self.repo: RAGRepository = repository

    def _normalize_embedding(self, embedding: list[float]) -> bytes:
        emb_np = np.array(embedding, dtype=np.float32)
        norm: float = float(np.linalg.norm(emb_np))
        if norm > 0:
            emb_np /= norm
        return emb_np.tobytes()

    def _read_chunks_from_stream(
        self, text_content: str
    ) -> abc.Generator[str, None, None]:
        buffer: list[str] = []
        for line in text_content.splitlines():
            buffer.extend(line.split())
            while len(buffer) >= 500:
                yield " ".join(buffer[:500])
                buffer = buffer[300:]
        if buffer:
            yield " ".join(buffer)

    async def process_and_save_file(self, file: UploadFile) -> int:
        content_bytes = await file.read()
        text_content = content_bytes.decode("utf-8")
        filename = file.filename or "unknown.txt"

        existing_hashes = await self.repo.get_existing_hashes()
        chunks_to_process: list[tuple[str, str, str]] = []

        for chunk in self._read_chunks_from_stream(text_content):
            chunk_hash = hashlib.md5(f"{chunk}:{filename}".encode()).hexdigest()
            if chunk_hash not in existing_hashes:
                chunks_to_process.append((chunk_hash, chunk, filename))

        if not chunks_to_process:
            return 0

        semaphore = asyncio.Semaphore(settings.CONCURRENCY)
        db_insert_data: list[tuple[str, str, str, bytes]] = []

        async def process_batch(
            batch: list[tuple[str, str, str]],
        ) -> list[tuple[str, str, str, bytes]]:
            async with semaphore:
                texts = [item[1] for item in batch]
                response = await openai_client.embeddings.create(
                    model=settings.EMBEDDING_MODEL_ID, input=texts
                )
                local_results = []
                for idx, data in enumerate(response.data):
                    ch_hash, ch_text, ch_name = batch[idx]
                    raw_emb = self._normalize_embedding(data.embedding)
                    local_results.append((ch_hash, ch_text, ch_name, raw_emb))
                return local_results

        batches = [
            chunks_to_process[i : i + settings.BATCH_SIZE]
            for i in range(0, len(chunks_to_process), settings.BATCH_SIZE)
        ]
        tasks = [process_batch(b) for b in batches]
        results = await asyncio.gather(*tasks)

        for batch_result in results:
            db_insert_data.extend(batch_result)

        await self.repo.save_embeddings_batch(db_insert_data)
        return len(db_insert_data)

    async def answer_question(self, question: str) -> tuple[str, list[str]]:
        db_rows = await self.repo.get_all_embeddings()
        if not db_rows:
            return "Database is empty. Please, load documents.", []

        all_chunks: list[str] = [row["chunk"] for row in db_rows]
        all_embeddings = np.array(
            [np.frombuffer(row["embedding"], dtype=np.float32) for row in db_rows]
        )

        query_response = await openai_client.embeddings.create(
            model=settings.EMBEDDING_MODEL_ID, input=question
        )
        query_emb_list = query_response.data[0].embedding
        query_embedding = np.array(query_emb_list, dtype=np.float32)

        q_norm = float(np.linalg.norm(query_embedding))
        if q_norm > 0:
            query_embedding /= q_norm

        similarities = np.dot(all_embeddings, query_embedding)
        top_k = min(2, len(similarities))

        if len(similarities) > top_k:
            top_indices = np.argpartition(similarities, -top_k)[-top_k:]
            top_indices = top_indices[np.argsort(-similarities[top_indices])]
        else:
            top_indices = np.argsort(-similarities)

        top_chunks = [all_chunks[int(idx)] for idx in top_indices]
        context = " ".join(top_chunks)

        chat_response = await openai_client.chat.completions.create(
            model=settings.MODEL_ID,
            messages=[
                {
                    "role": "user",
                    "content": f"Context: {context}\n\nQuestion: {question}\n\nAnswer:",
                }
            ],
        )

        answer = (
            chat_response.choices[0].message.content or "Failed to generate response"
        )
        return answer, top_chunks
