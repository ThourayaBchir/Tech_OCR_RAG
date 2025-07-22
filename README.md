# Ask Your Data: RAG Pipeline

A production-ready Retrieval-Augmented Generation (RAG) system for technical documents, featuring:

- **FastAPI** for API and streaming web UI  
- **Google Document AI OCR** (or alternative OCR backend)  
- **Qdrant** for fast vector search  
- **PostgreSQL** for chunk/document metadata  
- **Celery** for scalable, background document ingestion  
- **Internal Embedding Service** (using `fastembed`) with minimal dependencies  

---

## 🏗️ Core Logic Overview

1. **Document Ingestion (Celery Worker)**  
   - Reads PDFs/images from GCS or local storage.  
   - Calls Google Document AI OCR (or local OCR).  
   - Chunks the output into technical paragraphs and tables, ignoring images.  
   - Batches chunk embedding requests to an **internal embedding service** (running as a local microservice for efficiency and security).  
   - Stores vectors in Qdrant and chunk metadata in PostgreSQL.  
   - Tracks processing state by moving or tagging input files after success.

2. **Retrieval and QA Flow (FastAPI)**  
   - User submits a question via web UI or API.  
   - The query is embedded via the internal embedding service.  
   - Qdrant returns the top relevant chunks with associated metadata.  
   - A structured RAG prompt is constructed (chunks labeled as `[Source N]`, with filenames and page numbers).  
   - The LLM (OpenAI/Lambda or others) answers using only the retrieved context, with streaming SSE to the UI.  
   - References/citations are shown as clickable links, using signed GCS URLs if relevant.

---

## 🌟 Key Architecture Choices

- **Separation of Concerns**: Ingestion, embedding, retrieval, and serving are isolated into clear modules and services.  
- **Internal Embedding Service**:  
  - Embedding is handled by a lightweight FastAPI service using [`fastembed`](https://github.com/flagopen/fastembed).  
  - The service loads the model from a local persistent cache on startup.  
  - No outbound dependency on Hugging Face or OpenAI for embeddings at runtime.  
  - Makes batching and hardware acceleration easy, and simplifies local/cloud deployment.  
- **Batch Processing and Efficiency**:  
  - Chunking and embedding is batched (e.g., 64 at a time), for speed and API efficiency.  
  - Model is downloaded and cached once, then reused for all requests.  
- **Streaming Answers**:  
  - SSE (Server-Sent Events) streams tokens to the UI as soon as they arrive, for a smooth user experience.  
- **Reference Integrity**:  
  - Each answer cites sources as `[Source N]` with links to the original document and page, using signed URLs for privacy.

---

## 🗂 Project Structure

### Project Structure

- **`api/`**  
  FastAPI application, routes & schemas

- **`celery_tasks/`**  
  Document ingestion & pipeline Celery tasks

- **`llm/`**  
  Embedding & LLM client logic (prompt builder, OpenAI/Lambda calls)

- **`storage/`**  
  - **`db/`** — PostgreSQL models & data access  
  - **`vector/`** — Qdrant vector‐store logic

- **`io/`**  
  GCS, local file & other I/O helpers

- **`parsing/`**  
  OCR parsing & chunking logic

- **`services/`**  
  High-level ingestion, retrieval & search services

- **`utils/`**  
  Config, logging, batching & error-handling utilities

- **`embedding_service/`**  
  Minimal FastAPI service for internal text embedding

- **`static/`**  
  UI assets (e.g. `mac-ui.css`)

- **`tests/`**  
  Unit & integration tests


---

## 🚀 How to Start and Run

### 1. Clone and Setup
```bash
git clone <repo-url>
cd <repo-dir>
cp .env.example .env
# Fill out credentials and paths for GCS, LLM, DB, etc.
```

### 2. Download and Cache Embedding Model (One-time)
```bash

mkdir -p model-cache
docker run --rm -v $(pwd)/model-cache:/workspace python:3.11 \
  bash -c "pip install fastembed && python -c \"from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-base-en-v1.5', cache_dir='/workspace')\""
```

### 3. Build and Launch All Services
```bash
docker-compose up -d
```
This starts:

- FastAPI app (/infer endpoint and web UI)
- Celery worker for ingestion
- Qdrant, Postgres, Redis
- Internal embedding service (on port 9000)

UI available at http://localhost:8000/infer

### 4. Add Documents
Upload your PDFs/images to your GCS bucket (or local ingest folder).

Trigger the Celery ingestion task manually or periodically via Celery Beat.

### 5. Ask Questions!
Enter a technical question in the UI.

Answers are streamed with clickable, page-specific citations.



### 6. Some Details

Minimal dependencies in the embedding service: fastembed, fastapi, uvicorn.

Persistent storage for model cache, DB, and vector data is volume-mounted for easy migration and backup.

Signed URLs are used for all source document links when using GCS.

### License
MIT

