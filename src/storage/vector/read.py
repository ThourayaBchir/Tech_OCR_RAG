from qdrant_client import QdrantClient

qdrant_client = QdrantClient(host="qdrant", port=6333)


def search_chunks(query_embedding, collection="chunks", limit=5):
    """
    Searches Qdrant for the top-N most relevant chunks given a query embedding.
    Returns a list of dicts with text and metadata.
    """
    results = qdrant_client.search(
        collection_name=collection,
        query_vector=query_embedding,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
    return [
        {
            "id": hit.payload.get("id"),
            "text": hit.payload.get("text"),
            "type": hit.payload.get("type"),
            "page": hit.payload.get("page"),
            "score": hit.score,
        }
        for hit in results
    ]
