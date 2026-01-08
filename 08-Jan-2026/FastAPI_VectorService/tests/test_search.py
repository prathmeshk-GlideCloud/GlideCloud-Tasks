from httpx import AsyncClient, ASGITransport
from app.main import app


async def test_vector_search():
    payload = {
        "query": "How does FastAPI generate API documentation?",
        "top_k": 2
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/vectors/search", json=payload)

    assert response.status_code == 200
    body = response.json()

    assert "results" in body
    assert len(body["results"]) > 0

    top_text = body["results"][0]["text"].lower()
    assert "fastapi" in top_text
    assert "documentation" in top_text
