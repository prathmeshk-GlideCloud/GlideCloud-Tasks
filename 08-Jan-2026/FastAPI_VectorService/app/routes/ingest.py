from fastapi import APIRouter
from app.schemas import TextIngestRequest, IngestResponse
from app.services.vector_service import VectorService
import uuid

router = APIRouter(prefix="/vectors", tags=["Ingest"])


@router.post("/ingest", response_model=IngestResponse)
def ingest_text(payload: TextIngestRequest):
    document = {
        "id": str(uuid.uuid4()),
        "text": payload.text,
        "metadata": payload.metadata or {}
    }

    return VectorService.ingest_documents(
        documents=[document],
        chunk_size=payload.chunk_size,
        chunk_overlap=payload.chunk_overlap
    )
