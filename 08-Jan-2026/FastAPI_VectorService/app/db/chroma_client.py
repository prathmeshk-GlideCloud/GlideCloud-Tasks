# app/db/chroma_client.py

import chromadb
from chromadb.config import Settings
from app.config import CHROMA_COLLECTION_NAME

client = chromadb.Client(
    Settings(
        persist_directory="./chroma_store",
        anonymized_telemetry=False
    )
)

chroma_collection = client.get_or_create_collection(
    name=CHROMA_COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)
