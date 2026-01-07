from fastapi import APIRouter
from app.embeddings import get_embedding
from app.db.chroma_client import documents_collection, queries_collection
from app.schemas import SearchRequest
import uuid

router = APIRouter(tags=["search"])


@router.post("/search")
def search(request: SearchRequest):
    query_embedding = get_embedding(request.query)
    query_id = str(uuid.uuid4())

    queries_collection.add(
        documents=[request.query],
        embeddings=[query_embedding],
        ids=[query_id]
    )

    results = documents_collection.query(
        query_embeddings=[query_embedding],
        n_results=request.top_k
    )

    return {
        "query": request.query,
        "results": [
            {
                "document_id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "score": results["distances"][0][i]
            }
            for i in range(len(results["ids"][0]))
        ]
    }
