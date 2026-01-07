from fastapi import FastAPI
from app.routes.documents import router as documents_router
from app.routes.search import router as search_router
from app.routes.debug import router as debug_router

app = FastAPI(
    title="FastAPI Vector Database (Ollama + ChromaDB)",
    version="1.0"
)

app.include_router(documents_router)
app.include_router(search_router)
app.include_router(debug_router)
