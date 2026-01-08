from httpx import AsyncClient, ASGITransport
from app.main import app


async def test_vector_ingest():
    payload = {
        "documents": [
            {
                "id": "test_doc",
                "text": (
                    "FastAPI is a modern Python framework.\n\n"
                    "FastAPI provides automatic API documentation.\n\n"
                    "MongoDB is a NoSQL database."
                ),
                "metadata": {
                    "source": "pytest",
                    "topic": "backend"
                }
            }
        ],
        "chunk_size": 40,
        "chunk_overlap": 8
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/vectors/ingest", json=payload)

    assert response.status_code == 200
    body = response.json()

    assert body["documents_ingested"] == 1
    assert body["chunks_created"] >= 2
