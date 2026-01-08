from httpx import AsyncClient, ASGITransport
from app.main import app


async def test_docs_load():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/docs")
        assert response.status_code == 200
