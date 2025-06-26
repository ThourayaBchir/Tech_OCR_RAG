import logging

from cloud_io.gcs import download_json_from_gcs, list_gcs_json_files_recursively
from parsing.ocr_result import extract_text_and_tables

logger = logging.getLogger(__name__)


# def process_ocr_outputs_from_gcs(output_prefix: str):
#     """
#     Process all OCR JSONs written to a GCS output prefix.
#     Returns a list of all chunks from all results.
#     """
#     files = list_gcs_json_files_recursively(output_prefix)
#     chunks = []

#     for blob_name in files:
#         if not blob_name.endswith(".json"):
#             continue
#         try:
#             document_proto = download_json_from_gcs(blob_name)
#             doc_chunks = extract_text_and_tables(document_proto)
#             chunks.extend(doc_chunks)
#         except Exception as err:
#             logger.exception(f"Failed to parse {blob_name}: {err}")


#     return chunks
def process_ocr_outputs_from_gcs_yield(output_prefix: str):
    files = list_gcs_json_files_recursively(output_prefix)
    for blob_name in files:
        if not blob_name.endswith(".json"):
            continue
        try:
            document_proto = download_json_from_gcs(blob_name)
            doc_chunks = extract_text_and_tables(document_proto)
            for chunk in doc_chunks:
                yield chunk
        except Exception as err:
            logger.exception(f"Failed to parse {blob_name}: {err}")
