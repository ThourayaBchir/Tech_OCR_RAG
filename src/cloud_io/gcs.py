import json
import os
from datetime import timedelta

from google.cloud import storage

from utils.config import settings


def list_gcs_json_files_recursively(prefix: str):
    """
    Recursively list all JSON files under a GCS prefix (including nested folders).
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
    blobs = bucket.list_blobs(prefix=prefix)
    return [blob.name for blob in blobs if blob.name.endswith(".json")]


def download_json_from_gcs(blob_name: str):
    """Download and parse a JSON file from GCS."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
    blob = bucket.blob(blob_name)
    data = blob.download_as_bytes()
    return json.loads(data)


def move_gcs_blob(source_uri: str, target_prefix: str):
    """
    Move a file in GCS from its current location to target_prefix (folder).
    """
    storage_client = storage.Client()
    bucket_name = source_uri.split("/")[2]
    blob_name = "/".join(source_uri.split("/")[3:])
    bucket = storage_client.bucket(bucket_name)
    source_blob = bucket.blob(blob_name)

    filename = os.path.basename(blob_name)
    target_blob_name = os.path.join(target_prefix, filename)
    bucket.copy_blob(source_blob, bucket, target_blob_name)
    source_blob.delete()

    return f"gs://{bucket_name}/{target_blob_name}"


def get_output_prefix_for_pdf(blob_name: str):
    """
    Returns the expected OCR output prefix for a given PDF.
    E.g., 'output/filename.pdf/'
    """
    base = os.path.basename(blob_name)
    return f"output/{base}/"


def list_gcs_files_with_prefix(prefix: str, suffix=None):
    """
    List files in a bucket with a given prefix and optional suffix.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
    blobs = bucket.list_blobs(prefix=prefix)
    return [blob.name for blob in blobs if (not suffix or blob.name.endswith(suffix))]


def generate_gcs_signed_url(gs_path: str, expiration_seconds=600):
    """
    Given a gs:// URI, return a signed HTTP(s) URL valid for `expiration_seconds`.
    """
    if not gs_path.startswith("gs://"):
        raise ValueError("Input must start with gs://")
    parts = gs_path[5:].split("/", 1)
    if len(parts) != 2:
        raise ValueError("Invalid GCS URI")
    bucket_name, blob_name = parts
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(seconds=expiration_seconds),
        method="GET",
    )
    return url
