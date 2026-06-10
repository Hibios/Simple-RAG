from fastapi import APIRouter, Depends, File, UploadFile

from api.v1.dependencies import get_agent_service, get_rag_service
from schemas.rag import QueryRequest, QueryResponse, UploadResponse
from services.agent_service import ReActAgentService as RaS
from services.rag_service import RAGService

router: APIRouter = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/query", response_model=QueryResponse)
async def query_rag(
    payload: QueryRequest, service: RAGService = Depends(get_agent_service)
) -> QueryResponse:
    answer, sources = await service.answer_question(payload.question)
    return QueryResponse(answer=answer, sources=sources)


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...), service: RAGService = Depends(get_rag_service)
) -> UploadResponse:
    # TODO: It is advisable to download the file in the background
    chunks_created = await service.process_and_save_file(file)
    return UploadResponse(
        filename=file.filename or "unknown",
        status="success" if chunks_created > 0 else "skipped/no_new_chunks",
        document_id=chunks_created,
    )

@router.post("/chat")
async def chat_with_agent(question: str, 
                          agent_service: RaS = Depends(get_agent_service)
                          ) -> dict[str, str]:
    answer = await agent_service.run(question)
    return {"answer": answer}