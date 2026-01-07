import subprocess
import json

def get_embedding(text: str):
    process = subprocess.run(
        [
            "ollama",
            "run",
            "nomic-embed-text",
            text,
            "--format",
            "json"
        ],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    if process.returncode != 0:
        raise RuntimeError(process.stderr)

    output = process.stdout.strip()

    # 🔥 Ollama 0.13.5 returns a RAW LIST, not a dict
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        raise RuntimeError(f"Invalid JSON from Ollama: {output}")

    # If it's already a list, that's the embedding
    if isinstance(data, list):
        return data

    # Fallback for newer versions
    if isinstance(data, dict) and "embedding" in data:
        return data["embedding"]

    raise RuntimeError(f"Unexpected Ollama output format: {data}")
