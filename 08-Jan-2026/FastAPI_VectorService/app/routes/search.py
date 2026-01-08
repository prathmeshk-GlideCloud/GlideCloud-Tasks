from fastapi import APIRouter
from app.schemas import SearchRequest, SearchResponse
from app.services.vector_service import VectorService

router = APIRouter(tags=["Search"])

@router.post("/search", response_model=SearchResponse)
def search_vectors(payload: SearchRequest):
    results = VectorService.search(query=payload.query)

    return {
        "results": results
    }
