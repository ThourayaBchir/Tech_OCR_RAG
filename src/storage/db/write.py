from storage.db.models import Chunk
from storage.db.session import get_db_session


def insert_chunks_in_postgres(source_pdf: str, chunks: list):
    """
    Write chunk metadata to Postgres for traceability.
    """
    with get_db_session() as session:
        for chunk in chunks:
            chunk_record = Chunk(
                id=chunk["id"],
                source=source_pdf,
                type=chunk["type"],
                text=chunk["text"],
                page=chunk.get("page"),
            )
            session.add(chunk_record)
        session.commit()


def create_user(db: Session, username: str, password: str):
    user = User(username=username, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
