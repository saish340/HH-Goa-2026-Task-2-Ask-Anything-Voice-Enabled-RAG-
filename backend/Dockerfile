FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HUB_DISABLE_TELEMETRY=1 \
    AA_FORCE_CPU=1

WORKDIR /app

# Compilers needed for a few wheels on slim Debian.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend
COPY data/passages.jsonl ./data/passages.jsonl
COPY data/eval_queries.jsonl ./data/eval_queries.jsonl

# Build the offline FAISS + BM25 index during the image build (never at query
# time). Smaller limit => smaller image/RAM, good for free tiers.
#   docker build --build-arg INDEX_LIMIT=12000 .
ARG INDEX_LIMIT=12000
RUN python -m backend.app.ingestion.embed_and_index ${INDEX_LIMIT} \
    || echo "WARNING: build-time index failed; API will still boot with demo fallback"

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]