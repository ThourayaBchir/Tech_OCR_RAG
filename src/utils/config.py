# utils/config.py

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    SECRET_KEY = os.environ["SECRET_KEY"]
    GCP_PROJECT_ID = os.environ["GCP_PROJECT_ID"]
    GCP_DOC_LOCATION = os.environ["GCP_DOC_LOCATION"]
    GCP_DOC_PROCESSOR_ID = os.environ["GCP_DOC_PROCESSOR_ID"]
    GOOGLE_APPLICATION_CREDENTIALS = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    GCS_BUCKET_NAME = os.environ["GCS_BUCKET_NAME"]
    CELERY_BROKER_URL = os.environ["CELERY_BROKER_URL"]
    POSTGRES_DB = os.environ.get("POSTGRES_DB")
    POSTGRES_USER = os.environ.get("POSTGRES_USER")
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgres")
    POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
    LAMBDA_API_MODEL = os.environ.get("LAMBDA_API_MODEL")
    LAMBDA_API_KEY = os.environ.get("LAMBDA_API_KEY")
    LAMBDA_API_BASE = os.environ.get("LAMBDA_API_BASE")
    EMBEDDING_API_ENDPOINT = os.environ.get("EMBEDDING_API_ENDPOINT")
    EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL")
    EMBED_BATCH_LIMIT = os.environ.get("EMBED_BATCH_LIMIT")


settings = Settings()
