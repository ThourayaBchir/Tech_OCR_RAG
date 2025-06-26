# Ask Your Data: FastAPI RAG Pipeline

A production-ready Retrieval-Augmented Generation (RAG) service for technical documents, combining:

- **FastAPI** (REST API & web UI)
- **Google Document AI OCR** for high-quality PDF/image text extraction
- **Qdrant** for fast vector search
- **PostgreSQL** for chunk/document metadata
- **Celery** for scalable document ingestion and processing
- **Google Cloud Storage** for document input/output

## Features

- Ingest scanned PDFs/images, extract clean paragraphs/tables, chunk & vectorize
- Fast, accurate search and RAG-style question answering over your documents
- References are cited as `[Source N]`, each linked to a time-limited, secure GCS download
- Streaming responses in the UI

