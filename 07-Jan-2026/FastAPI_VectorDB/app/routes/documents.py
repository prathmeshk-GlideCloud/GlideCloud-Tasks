from fastapi import APIRouter
from app.embeddings import get_embedding
from app.db.chroma_client import documents_collection
from app.schemas import AddDocumentRequest
import uuid

router = APIRouter(tags=["documents"])


@router.post("/add-document")
def add_document(request: AddDocumentRequest):
    embedding = get_embedding(request.text)
    doc_id = str(uuid.uuid4())

    documents_collection.add(
        documents=[request.text],
        embeddings=[embedding],
        ids=[doc_id]
    )

    return {
        "status": "stored",
        "document_id": doc_id,
        "embedding_dim": len(embedding)
    }
