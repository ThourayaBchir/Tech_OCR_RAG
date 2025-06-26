from storage.db.models import Chunk
from storage.db.session import get_db_session


def get_chunk_sources(chunk_ids: list):
    """
    Given a list of chunk IDs, fetch their 'source' (document name) from Postgres.
    Returns a dict mapping chunk_id -> source_pdf.
    """
    with get_db_session() as session:
        result = (
            session.query(Chunk.id, Chunk.source).filter(Chunk.id.in_(chunk_ids)).all()
        )
        return {row.id: row.source for row in result}
