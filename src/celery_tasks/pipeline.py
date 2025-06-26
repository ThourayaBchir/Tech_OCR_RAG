import logging
from this import d

from celery_tasks.scheduling import celery_app
from cloud_io.gcp_ocr import batch_process_pdf_gcs
from cloud_io.gcs import list_gcs_files_with_prefix, move_gcs_blob
from llm.embeddings import embed_texts_batched
from services.ingestion_service import process_ocr_outputs_from_gcs_yield
from storage.db.write import insert_chunks_in_postgres
from storage.vector.write import upsert_chunks_in_qdrant
from utils.batch import batch_iterable
from utils.config import settings

logger = logging.getLogger(__name__)


BATCH_SIZE = 64  # Match embedding service


@celery_app.task(name="ingest.ocr_pdf")
def ocr_pdf_task(gcs_input: str):
    """
    1. Run batch OCR, writing output to GCS.
    2. Move PDF to 'ocr_done/' folder on success.
    3. Chain to chunk/embedding step immediately.
    """
    try:
        output_prefix = batch_process_pdf_gcs(gcs_input)
        logger.info(f"OCR complete for {gcs_input}, output at {output_prefix}")

        new_uri = move_gcs_blob(gcs_input, "ocr_done")
        logger.info(f"Moved {gcs_input} to {new_uri}")

        # Chain: immediately kick off next step
        chunk_embed_pipeline_task.delay(output_prefix, new_uri)

        return {"output_prefix": output_prefix, "source_pdf": new_uri}

    except Exception as err:
        logger.exception(f"OCR task failed for {gcs_input}: {err}")
        raise


@celery_app.task(name="ingest.chunk_embed_pipeline")
def chunk_embed_pipeline_task(output_prefix: str, source_pdf: str):
    """
    For each batch of chunks in output_prefix:
      - Embed
      - Upsert to Qdrant
      - Write metadata to Postgres
    Moves source_pdf from 'ocr_done/' to 'processed/' when done.
    """
    try:
        chunk_generator = process_ocr_outputs_from_gcs_yield(output_prefix)
        total_chunks = 0

        for chunk_batch in batch_iterable(chunk_generator, BATCH_SIZE):
            chunk_texts = [c["text"] for c in chunk_batch]
            embeddings = embed_texts_batched(chunk_texts)
            upsert_chunks_in_qdrant(
                collection="chunks", chunks=chunk_batch, embeddings=embeddings
            )

            insert_chunks_in_postgres(source_pdf=source_pdf, chunks=chunk_batch)
            total_chunks += len(chunk_batch)

        logger.info(f"Chunked/embedded {total_chunks} for {source_pdf}")
        move_gcs_blob(source_pdf, "processed")
        logger.info(f"Moved {source_pdf} to processed/")

    except Exception as err:
        logger.exception(f"Pipeline task failed for {source_pdf}: {err}")
        raise


@celery_app.task(name="ingest.schedule_ocr")
def schedule_ocr_tasks():
    """
    Periodically scan '/' for new PDFs and kick off OCR task for each.
    """
    pdfs = list_gcs_files_with_prefix("", suffix=".pdf")
    for blob_name in pdfs:
        gcs_uri = f"gs://{settings.GCS_BUCKET_NAME}/{blob_name}"
        ocr_pdf_task.delay(gcs_uri)
