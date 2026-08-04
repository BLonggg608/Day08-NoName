"""Shared local/OpenRouter embedding provider for Tasks 4 and 5."""

import os
import numpy as np
import requests
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local").strip().lower()
LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "BAAI/bge-m3")
OPENROUTER_EMBEDDING_MODEL = os.getenv("OPENROUTER_EMBEDDING_MODEL", "openai/text-embedding-3-small")

def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if EMBEDDING_PROVIDER == "local":
        model = SentenceTransformer(LOCAL_EMBEDDING_MODEL)
        return np.asarray(model.encode(texts, normalize_embeddings=True), dtype=np.float32).tolist()
    if EMBEDDING_PROVIDER != "openrouter":
        raise ValueError("EMBEDDING_PROVIDER must be 'local' or 'openrouter'")
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key or key == "sk-or-v1-...":
        raise RuntimeError("OPENROUTER_API_KEY is required for OpenRouter embeddings")
    response = requests.post(
        "https://openrouter.ai/api/v1/embeddings",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": OPENROUTER_EMBEDDING_MODEL, "input": texts},
        timeout=120,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"OpenRouter embeddings failed ({response.status_code}): {response.text[:300]}")
    data = response.json().get("data")
    if not isinstance(data, list) or len(data) != len(texts):
        raise RuntimeError("OpenRouter returned an invalid embedding response")
    data.sort(key=lambda item: item.get("index", 0))
    return [item["embedding"] for item in data]

def embedding_description() -> str:
    return (f"local:{LOCAL_EMBEDDING_MODEL}" if EMBEDDING_PROVIDER == "local"
            else f"openrouter:{OPENROUTER_EMBEDDING_MODEL}")
