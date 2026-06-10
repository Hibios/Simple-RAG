import aiosqlite
from fastapi import Depends

from core.database import get_db_session
from repositories.rag_repository import RAGRepository
from services.agent_service import ReActAgentService
from services.rag_service import RAGService


async def get_rag_service(
    db: aiosqlite.Connection = Depends(get_db_session),
) -> RAGService:
    repository = RAGRepository(db)
    return RAGService(repository)

async def get_agent_service(rag_service: RAGService = Depends(get_rag_service)
                            ) -> ReActAgentService:
    return ReActAgentService(rag_service)