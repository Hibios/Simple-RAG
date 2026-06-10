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

TODOs:
- Implement file size validation, background file uploading, CORS, and role-based backend authorization.
- Use external Key Management Service (KMS), External Secrets Operator (ESO) (like HashiCorp Vault), and valueFrom.secretKeyRef.
- Save logs to files and forward them to log management systems like ELK.
- Improve and better configure Startup Probe, Liveness Probe, and Readiness Probe.
- Add Prometheus metrics hosted on a separate web server at /metrics, set up logging with Fluentbit, and implement OpenTelemetry (OTel) with Jaeger if necessary.
- Utilize Kubernetes Persistent Volumes and low-latency block storage.
- Categorically migrate from SQLite to dedicated Vector Databases like Qdrant with algorithms like FAISS and HNSW, implement cluster scaling and load balancing; currently, proper Pod scaling is constrained.
- Keep the FastAPI container isolated on an unencrypted port (e.g., EXPOSE 8000) accepting raw HTTP inside the internal cluster network; offload all SSL/TLS handshakes (443 -> 8000) onto the edge boundary layer: a Kubernetes Ingress Controller (Nginx, Traefik), AWS Application Load Balancer (ALB), or Cloudflare.
