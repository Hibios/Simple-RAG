from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(
        ..., min_length=3, description="User question to the knowledge base"
    )


class QueryResponse(BaseModel):
    answer: str = Field(..., description="Generated response from the RAG system")
    sources: list[str] = Field(default_factory=list, description="List of sources")


class UploadResponse(BaseModel):
    filename: str
    status: str
    document_id: int
