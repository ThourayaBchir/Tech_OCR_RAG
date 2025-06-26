import logging

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams

logger = logging.getLogger(__name__)


qdrant_client = QdrantClient(host="qdrant", port=6333)

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


def ensure_qdrant_collection(client, collection_name, vector_size, distance):
    # Accept Distance enum or string; coerce if needed
    if isinstance(distance, str):
        distance = Distance[distance.upper()]
    existing_collections = [c.name for c in client.get_collections().collections]
    if collection_name not in existing_collections:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=distance),
        )


def upsert_chunks_in_qdrant(collection, chunks, embeddings):
    """
    Write each chunk+embedding as a point to Qdrant.
    """

    # Ensure the collection exists before upsert
    ensure_qdrant_collection(
        client=qdrant_client,
        collection_name=collection,
        vector_size=len(embeddings[0]),
        distance=Distance.COSINE,
    )
    print("collection_name -- len chunks", collection, len(chunks))

    points = []
    for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
        point = PointStruct(
            id=chunk["id"],  # assign a unique id
            vector=vector,
            payload={
                "id": chunk["id"],
                "type": chunk["type"],
                "text": chunk["text"],
                "page": chunk.get("page"),
            },
        )
        points.append(point)

    qdrant_client.upsert(collection_name=collection, points=points)

    logger.info(f"Upserted {len(chunks)} chunks to Qdrant collection '{collection}'")
