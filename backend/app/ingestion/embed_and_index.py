"""Offline chunking + embedding + indexing.

Builds the multi-strategy chunk index and writes these artifacts:

- ``data/chunks.jsonl``  — every chunk with its metadata (aligned with FAISS order)
- ``data/index.faiss``   — FAISS dense index over chunk embeddings
- ``data/index_meta.json`` — build-time stats

Run once before serving (never at query time). Example:

    python -m backend.app.ingestion.embed_and_index 2500
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, List

import faiss
import numpy as np

from backend.app.config import (
    CHUNKS_PATH,
    DATA_DIR,
    EMBEDDING_DIM,
    INDEX_PATH,
    PASSAGES_PATH,
)
from backend.app.ingestion.chunkers.semantic import semantic_chunker
from backend.app.ingestion.chunkers.sentence import sentence_chunker, split_sentences
from backend.app.ingestion.chunkers.sliding_window import sliding_window_chunker
from backend.app.retrieval.embeddings import embed_texts

META_PATH = DATA_DIR / "index_meta.json"


def load_passages(limit: int | None = None) -> List[dict]:
    with open(PASSAGES_PATH, encoding="utf-8") as f:
        passages = [json.loads(line) for line in f]
    if limit is not None:
        passages = passages[:limit]
    return passages


def _sentence_embedding_map(passages: List[dict], batch_size: int = 256) -> dict:
    unique: dict[str, bool] = {}
    for p in passages:
        for s in split_sentences(p["text"]):
            unique.setdefault(s, True)
    keys = list(unique)
    vectors = embed_texts(keys, batch_size=batch_size)
    return dict(zip(keys, vectors))


def build_chunks(passages: List[dict], sentence_embeddings: dict) -> List[dict]:
    chunks: List[dict] = []
    for p in passages:
        text = p["text"]
        doc_id = str(p["passage_id"])
        emb_fn = sentence_embeddings.get

        chunks.extend(sentence_chunker(text, document_id=doc_id, language=p.get("language", "en")))
        chunks.extend(
            semantic_chunker(
                text,
                document_id=doc_id,
                language=p.get("language", "en"),
                embed_fn=emb_fn,
            )
        )
        chunks.extend(sliding_window_chunker(text, document_id=doc_id, language=p.get("language", "en")))
    return chunks


def build_index(max_passages: int | None = None) -> dict[str, Any]:
    t0 = time.time()
    passages = load_passages(max_passages)

    print(f"Chunking {len(passages)} passages across 3 strategies ...")
    sentence_embeddings = _sentence_embedding_map(passages)
    chunks = build_chunks(passages, sentence_embeddings)

    print(f"Embedding {len(chunks)} chunks ...")
    chunk_texts = [c["text"] for c in chunks]
    matrix = embed_texts(chunk_texts, batch_size=256)

    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    index.add(matrix)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    per_strategy: dict[str, int] = {}
    for c in chunks:
        per_strategy[c["chunk_strategy"]] = per_strategy.get(c["chunk_strategy"], 0) + 1

    meta = {
        "passages": len(passages),
        "chunks": len(chunks),
        "per_strategy": per_strategy,
        "embedding_dim": EMBEDDING_DIM,
        "build_seconds": round(time.time() - t0, 1),
    }
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    return meta


if __name__ == "__main__":
    import sys

    K = int(sys.argv[1]) if len(sys.argv) > 1 else None
    print(build_index(K))