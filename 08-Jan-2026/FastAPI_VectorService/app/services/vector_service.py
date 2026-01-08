# app/services/vector_service.py

from typing import List, Dict, Any

from app.services.chunking_service import prepare_chunks
from app.embeddings import get_embedding
from app.db.chroma_client import chroma_collection
from app.config import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_TOP_K,
)


class VectorService:
    """
    Core orchestration layer for vector ingestion and search.
    """

    @staticmethod
    def ingest_documents(
        *,
        documents: List[Dict[str, Any]],
        chunk_size: int | None = None,      # interpreted as max_words
        chunk_overlap: int | None = None,   # interpreted as overlap_words
    ) -> Dict[str, int]:
        """
        Ingests documents into the vector database.
        """

        max_words = chunk_size or DEFAULT_CHUNK_SIZE
        overlap_words = chunk_overlap or DEFAULT_CHUNK_OVERLAP

        total_chunks = 0
        total_documents = len(documents)

        for doc in documents:
            text = doc["text"]
            metadata = doc.get("metadata", {})
            doc_id = doc.get("id")

            prepared_chunks_list = prepare_chunks(
                text=text,
                metadata=metadata,
                max_words=max_words,
                overlap_words=overlap_words,
                doc_id=doc_id,
            )

            if not prepared_chunks_list:
                continue

            texts = [chunk["text"] for chunk in prepared_chunks_list]
            metadatas = [chunk["metadata"] for chunk in prepared_chunks_list]
            ids = [chunk["id"] for chunk in prepared_chunks_list]

            embeddings = [get_embedding(t) for t in texts]

            chroma_collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )

            total_chunks += len(prepared_chunks_list)

        return {
            "documents_ingested": total_documents,
            "chunks_created": total_chunks,
        }

    @staticmethod
    def search(*, query: str) -> list[dict]:
        query_embedding = get_embedding(query)

        results = chroma_collection.query(
            query_embeddings=[query_embedding],
            n_results=10  # internal fetch, not exposed to user
        )

        formatted_results = []

        for i in range(len(results["documents"][0])):
            distance = results["distances"][0][i]

            similarity = round(1 / (1 + distance), 4)

            formatted_results.append({
                "text": results["documents"][0][i],
                "score": similarity,
                "metadata": results["metadatas"][0][i],
            })

        # sort by relevance
        formatted_results.sort(key=lambda x: x["score"], reverse=True)

        # assign rank AFTER sorting
        for idx, r in enumerate(formatted_results, start=1):
            r["rank"] = idx

        return formatted_results
