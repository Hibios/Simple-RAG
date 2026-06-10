import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio

async def test_system_health_endpoints(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}

    response = await async_client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"

async def test_upload_document_workflow(async_client: AsyncClient) -> None:
    file_content = (
        "The secret code to access the laboratory vault is 9944-X.\n"
        "Don Quixote told Sancho Panza that true courage is facing reality.\n"
        "The project codename for the new AI system is Project Genesis."
    )
    files = {"file": ("test_doc.txt", file_content.encode("utf-8"), "text/plain")}
    
    response = await async_client.post("/api/v1/rag/upload", files=files)
    assert response.status_code == 200
    
    data = response.json()
    assert data["filename"] == "test_doc.txt"
    assert data["status"] == "success"
    assert data["document_id"] > 0

async def test_upload_duplicate_document_skips(async_client: AsyncClient) -> None:
    file_content = (
        "The secret code to access the laboratory vault is 9944-X.\n"
        "Don Quixote told Sancho Panza that true courage is facing reality.\n"
        "The project codename for the new AI system is Project Genesis."
    )
    files = {"file": ("test_doc.txt", file_content.encode("utf-8"), "text/plain")}
    
    response = await async_client.post("/api/v1/rag/upload", files=files)
    assert response.status_code == 200
    assert response.json()["status"] == "skipped/no_new_chunks"

async def test_chat_with_agent_execution_loop(async_client: AsyncClient) -> None:
    params = {"question": "What is the secret code to access the laboratory vault?"}
    response = await async_client.post("/api/v1/rag/chat", params=params)
    assert response.status_code == 200
    
    data = response.json()
    assert "answer" in data
    assert "9944-X" in data["answer"]

async def test_agent_handles_unknown_context(async_client: AsyncClient) -> None:
    params = {"question": "What did Don Quixote say to Sancho Panza?"}
    response = await async_client.post("/api/v1/rag/chat", params=params)
    assert response.status_code == 200
    
    data = response.json()
    assert "answer" in data
    
    answer_lower = data["answer"].lower()
    assert "sancho" in answer_lower
    assert "courage" in answer_lower or "reality" in answer_lower
