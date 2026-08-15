"""Download and cache MSMARCO-XI dataset from Hugging Face."""

import json
import os
from pathlib import Path

# Try importing datasets, fallback if not available
try:
    from datasets import load_dataset
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
MSMARCO_CACHE = DATA_DIR / "msmarco_xi.jsonl"


def download_msmarco_xi(split: str = "train", limit: int = 500) -> list[dict]:
    """
    Download MSMARCO-XI dataset from Hugging Face.
    
    Args:
        split: "train" or "test"
        limit: max number of docs to download (for demo, use 500; for prod, use full)
    
    Returns:
        List of document dicts with id, text, and metadata
    """
    if not HAS_DATASETS:
        print("⚠️  datasets library not installed. Using fallback test data.")
        return get_fallback_data()

    try:
        print(f"📥 Downloading MSMARCO-XI ({split} split)...")
        dataset = load_dataset("ai4bharat/MSMARCO-XI", "en", split=split, streaming=False)
        
        docs = []
        for i, item in enumerate(dataset):
            if i >= limit:
                break
            docs.append({
                "document_id": f"doc_{i}",
                "text": item.get("text", item.get("content", "")),
                "passage_id": item.get("passage_id", ""),
                "language": "en",
            })
        
        print(f"✓ Downloaded {len(docs)} documents")
        return docs
    except Exception as e:
        print(f"❌ Failed to download: {e}")
        return get_fallback_data()


def get_fallback_data() -> list[dict]:
    """Return test data if dataset unavailable."""
    return [
        {"document_id": "doc_0", "text": "Paris is the capital city of France and is located on the Seine River.", "language": "en"},
        {"document_id": "doc_1", "text": "New Delhi is the capital of India and serves as the political center.", "language": "en"},
        {"document_id": "doc_2", "text": "Water boils at 100 degrees Celsius (212 Fahrenheit) at standard atmospheric pressure.", "language": "en"},
        {"document_id": "doc_3", "text": "The Eiffel Tower is an iconic monument in Paris, France, built in 1889.", "language": "en"},
        {"document_id": "doc_4", "text": "India is a country in South Asia with a population of over 1.4 billion people.", "language": "en"},
        {"document_id": "doc_5", "text": "Chemistry is the science that studies matter and reactions between substances.", "language": "en"},
        {"document_id": "doc_6", "text": "The moon orbits Earth and influences ocean tides through gravitational pull.", "language": "en"},
        {"document_id": "doc_7", "text": "Python is a popular programming language used for web development and data science.", "language": "en"},
    ]


def cache_dataset(docs: list[dict]) -> None:
    """Save dataset to local JSONL cache."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(MSMARCO_CACHE, "w") as f:
        for doc in docs:
            f.write(json.dumps(doc) + "\n")
    print(f"✓ Cached {len(docs)} docs to {MSMARCO_CACHE}")


def load_cached_dataset() -> list[dict]:
    """Load dataset from local cache."""
    if not MSMARCO_CACHE.exists():
        print("⚠️  No cached dataset found. Downloading...")
        docs = download_msmarco_xi()
        cache_dataset(docs)
        return docs
    
    docs = []
    with open(MSMARCO_CACHE) as f:
        for line in f:
            docs.append(json.loads(line))
    print(f"✓ Loaded {len(docs)} docs from cache")
    return docs


if __name__ == "__main__":
    docs = load_cached_dataset()
    print(f"\n📊 Dataset stats:")
    print(f"  Total docs: {len(docs)}")
    if docs:
        print(f"  Sample: {docs[0]}")
