FROM python:3.11-slim

WORKDIR /app

# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

RUN python -m venv /app/venv


COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

ENV PYTHONPATH="/app/src"


RUN useradd -m appuser && chown -R appuser /app
USER appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Entrypoint/CMD will be set via docker-compose.yml
