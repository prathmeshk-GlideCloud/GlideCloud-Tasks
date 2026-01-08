from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


# ---------- INGESTION SCHEMAS ----------

class TextIngestRequest(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = {}
    chunk_size: int = 500
    chunk_overlap: int = 50



class IngestResponse(BaseModel):
    documents_ingested: int
    chunks_created: int


# ---------- SEARCH SCHEMAS ----------

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")




class SearchResult(BaseModel):
    rank: int = Field(
        ...,
        description="Rank of the result based on relevance"
    )
    text: str = Field(
        ...,
        description="Retrieved text chunk"
    )
    score: float = Field(
        ...,
        description="Similarity score (higher is more relevant)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata associated with the chunk"
    )


class SearchResponse(BaseModel):
    results: List[SearchResult]
