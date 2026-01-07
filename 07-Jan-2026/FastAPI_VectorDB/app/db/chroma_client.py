import chromadb
from chromadb.config import Settings

client = chromadb.Client(
    Settings(
        persist_directory="./chroma_store",
        anonymized_telemetry=False
    )
)

documents_collection = client.get_or_create_collection(
    name="documents"
)

queries_collection = client.get_or_create_collection(
    name="queries"
)
