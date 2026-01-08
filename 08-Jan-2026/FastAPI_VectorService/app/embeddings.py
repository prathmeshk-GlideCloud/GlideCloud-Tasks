# app/embeddings.py

import requests
from app.config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL


def get_embedding(text: str) -> list[float]:
    """
    Generate embeddings using Ollama (remote or local).
    """

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={
            "model": OLLAMA_EMBED_MODEL,
            "prompt": text
        },
        timeout=60
    )

    response.raise_for_status()

    return response.json()["embedding"]
