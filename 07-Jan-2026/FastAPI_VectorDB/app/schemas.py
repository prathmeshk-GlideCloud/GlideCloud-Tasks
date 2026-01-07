from pydantic import BaseModel


class AddDocumentRequest(BaseModel):
    text: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 3
