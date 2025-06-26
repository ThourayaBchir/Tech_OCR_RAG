import logging
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastembed import TextEmbedding
from pydantic import BaseModel, conlist

from utils.config import settings

# Logging config
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("embedding_api")

# Model and config
MODEL_NAME = settings.EMBEDDING_MODEL
BATCH_LIMIT = int(settings.EMBED_BATCH_LIMIT)


try:
    _cached_model = TextEmbedding(
        model_name=MODEL_NAME,
        cache_dir="/app/nlp",
        local_dir="/app/nlp",
        local_files_only=True,
        max_workers=1,
    )

    logger.info(f"Loaded model: {MODEL_NAME}")
except Exception as e:
    logger.error(f"Failed to load embedding model '{MODEL_NAME}': {e}")
    raise

# FastAPI setup
app = FastAPI(title="Qdrant FastEmbed Service", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EmbedRequest(BaseModel):
    texts: conlist(str, min_length=1, max_length=BATCH_LIMIT)


class EmbedResponse(BaseModel):
    model: str
    embeddings: list[list[float]]


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/embed", response_model=EmbedResponse)
def embed_texts(request: EmbedRequest):
    """
    Batch embed up to BATCH_LIMIT texts.
    """
    texts = request.texts
    if not texts or len(texts) > BATCH_LIMIT:
        raise HTTPException(
            status_code=400,
            detail=f"Must provide 1 to {BATCH_LIMIT} texts per request.",
        )

    try:
        vectors = list(_cached_model.embed(texts))
        logger.info("Embedded %d texts (model=%s)", len(texts), MODEL_NAME)
        return {"model": MODEL_NAME, "embeddings": vectors}
    except Exception as e:
        logger.exception("Embedding error")
        raise HTTPException(status_code=500, detail=f"Embedding error: {e}")


@app.exception_handler(Exception)
def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500, content={"detail": f"Internal server error: {exc}"}
    )
