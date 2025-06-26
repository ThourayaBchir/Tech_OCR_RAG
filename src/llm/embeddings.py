import requests

from utils.config import settings


def batch(iterable, batch_size):
    """Yield successive batches of batch_size from iterable."""
    for i in range(0, len(iterable), batch_size):
        yield iterable[i : i + batch_size]


def embed_texts_batched(texts, endpoint=settings.EMBEDDING_API_ENDPOINT, batch_size=64):
    all_embeddings = []
    for text_batch in batch(texts, batch_size):
        resp = requests.post(endpoint, json={"texts": text_batch}, timeout=60)
        try:
            resp.raise_for_status()
        except requests.HTTPError as err:
            print(f"Embedding service error {resp.status_code}: {resp.text}")
            raise
        all_embeddings.extend(resp.json()["embeddings"])
    return all_embeddings


def embed_texts_remote(texts, endpoint=settings.EMBEDDING_API_ENDPOINT):
    """
    Calls the embedding_api to embed one or more texts.
    Returns a list of embeddings.
    """
    resp = requests.post(endpoint, json={"texts": texts}, timeout=60)
    resp.raise_for_status()
    return resp.json()["embeddings"]
