import logging
import os

from google.cloud import documentai_v1 as documentai
from google.cloud import storage

from utils.config import settings
from utils.exceptions import DocumentProcessingError

logger = logging.getLogger(__name__)


def batch_process_pdf_gcs(gcs_input_uri: str) -> str:
    """
    Asynchronously process a PDF in GCS via Document AI OCR and write results to GCS.

    Args:
        gcs_input_uri (str): URI of the PDF in GCS, e.g. "gs://my-bucket/file.pdf".

    Returns:
        str: GCS prefix where output JSON was written.
             e.g. "gs://my-bucket/output/file/"

    Raises:
        DocumentProcessingError: on any failure.
    """

    # Build client and resource names
    client = documentai.DocumentProcessorServiceClient(
        client_options={"api_endpoint": "eu-documentai.googleapis.com"}
    )
    name = client.processor_path(
        settings.GCP_PROJECT_ID,
        settings.GCP_DOC_LOCATION,
        settings.GCP_DOC_PROCESSOR_ID,
    )

    # Configure input from GCS
    gcs_doc = documentai.GcsDocument(gcs_uri=gcs_input_uri, mime_type="application/pdf")
    gcs_docs = documentai.GcsDocuments(documents=[gcs_doc])
    input_config = documentai.BatchDocumentsInputConfig(gcs_documents=gcs_docs)

    # Configure output to GCS under a per-file prefix
    bucket = settings.GCS_BUCKET_NAME
    filename = os.path.basename(gcs_input_uri)
    output_prefix = f"output/{filename}/"
    gcs_output_config = documentai.DocumentOutputConfig.GcsOutputConfig(
        gcs_uri=f"gs://{bucket}/{output_prefix}"
    )
    output_config = documentai.DocumentOutputConfig(gcs_output_config=gcs_output_config)

    # Build the batch request
    request = documentai.BatchProcessRequest(
        name=name,
        input_documents=input_config,
        document_output_config=output_config,
    )

    try:
        # Kick off the batch operation
        operation = client.batch_process_documents(request=request)
        logger.info(f"Started batch OCR for {gcs_input_uri}, waiting for completion...")
        operation.result(timeout=300)  # wait up to 5 minutes

        logger.info(f"Batch OCR completed for {gcs_input_uri}")
        return output_prefix  # f"gs://{bucket}/{output_prefix}"

    except Exception as err:
        logger.exception(f"Batch OCR failed for {gcs_input_uri}")
        raise DocumentProcessingError(f"Batch OCR failed for {gcs_input_uri}") from err


def move_gcs_blob_to_processed(gcs_uri: str) -> None:
    """
    Move a blob in GCS into a 'processed/' subfolder.

    Args:
        gcs_uri (str): Full GCS URI, e.g. 'gs://bucket-name/file.pdf'.
    """

    try:
        client = storage.Client()
        path = gcs_uri.replace("gs://", "")
        bucket_name, blob_name = path.split("/", 1)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        new_name = f"processed/{os.path.basename(blob_name)}"
        bucket.rename_blob(blob, new_name)
        logger.info(f"Moved {gcs_uri} to gs://{bucket_name}/{new_name}")

    except Exception as err:
        logger.exception(f"Failed to move {gcs_uri} to processed/")
        raise DocumentProcessingError(
            f"Failed to move {gcs_uri} to processed/"
        ) from err
