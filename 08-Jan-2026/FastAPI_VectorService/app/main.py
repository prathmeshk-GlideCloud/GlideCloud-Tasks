from fastapi import FastAPI
from app.routes.ingest import router as ingest_router
from app.routes.search import router as search_router

app = FastAPI(
    title="FastAPI Vector Service",
    version="1.0"
)


app.include_router(ingest_router, prefix="/vectors", tags=["Ingest"])
app.include_router(search_router, prefix="/vectors", tags=["Search"])
