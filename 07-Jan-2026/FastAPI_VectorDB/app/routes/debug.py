from fastapi import APIRouter
from app.db.chroma_client import documents_collection, queries_collection

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/documents")
def debug_documents():
    data = documents_collection.get(include=["documents", "embeddings"])

    if not data["ids"]:
        return []

    response = []
    for i in range(len(data["ids"])):
        preview = data["embeddings"][i][:5]

        # 🔥 CRITICAL FIX: cast to float
        preview = [float(x) for x in preview]

        response.append({
            "document_id": data["ids"][i],
            "text": data["documents"][i],
            "embedding_preview": preview
        })

    return response


@router.get("/queries")
def debug_queries():
    data = queries_collection.get(include=["documents", "embeddings"])

    if not data["ids"]:
        return []

    response = []
    for i in range(len(data["ids"])):
        preview = data["embeddings"][i][:5]
        preview = [float(x) for x in preview]

        response.append({
            "query_id": data["ids"][i],
            "query": data["documents"][i],
            "embedding_preview": preview
        })

    return response
