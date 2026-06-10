# QnA RAG Microservice (Review Ready)

An asynchronous **FastAPI** microservice implementing a core **RAG (Retrieval-Augmented Generation)** loop and an autonomous **ReAct Agent** using native OpenAI Function Calling (Tools) without third-party frameworks like LangChain or LlamaIndex.

---

## Environment Startup & Validation

### 1. Configure Secret Scope
Define a local `.env` file at the project root folder (parallel to the `src` folder):
```text
SIMPLE_RAG_MODEL_ID="meta-llama/Llama-3.3-70B-Instruct:groq"
SIMPLE_RAG_EMBEDDING_MODEL_ID="intfloat/multilingual-e5-large"
SIMPLE_RAG_OPENAI_API_URL="https://openrouter.ai/api/v1"
SIMPLE_RAG_OPENAI_KEY="api_token_here"

# If local models LM Studio / Ollama, meta-llama-3.1-8b-instruct, text-embedding-bge-m3
# SIMPLE_RAG_OPENAI_API_URL=http://172.30.128.1:1234/v1
```

### 2. Runtime Lifecycle Commands
* **Enforce Clean Build Extraction**:
  ```bash
  docker compose build --no-cache
  ```
* **Boot Container Architecture**:
  ```bash
  docker compose up
  ```

Swagger interactive UI exposes API specs directly at: **`http://localhost:8000/docs`**.

---

## Testing & Code Verification
Testing routines completely isolate the database. During execution, `pytest` substitutes the dependencies provider with an in-memory transactional database leveraging shared instance streaming: `file:test_db?mode=memory&cache=shared`.
* **Execute Asynchronous Integration Suite (`anyio` context)**:
  ```bash
  uv run pytest --tb=short -v tests/test_rag.py
  ```
* **Execute Strict Static Compliance Check (`mypy`)**:
  ```bash
  uv run mypy src tests
  ```

---
