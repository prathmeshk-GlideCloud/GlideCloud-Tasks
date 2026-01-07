import requests
from app.config import (
    OLLAMA_BASE_URL,
    OLLAMA_EMBED_MODEL,
    OLLAMA_TIMEOUT,
)


def get_embedding(text: str) -> list[float]:
    """
    Generate embeddings using Ollama HTTP API.
    Ollama runs as a private service.
    """

    url = f"{OLLAMA_BASE_URL}/api/embeddings"

    payload = {
        "model": OLLAMA_EMBED_MODEL,
        "prompt": text,
    }

    response = requests.post(
        url,
        json=payload,
        timeout=OLLAMA_TIMEOUT,
    )
    response.raise_for_status()

    data = response.json()

    if "embedding" not in data:
        raise RuntimeError(f"Invalid Ollama response: {data}")

    return data["embedding"]
