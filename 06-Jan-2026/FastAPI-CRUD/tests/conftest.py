import pytest
import mongomock
from fastapi.testclient import TestClient

import db
from main import app


@pytest.fixture(scope="function")
def test_client(monkeypatch):
    mock_client = mongomock.MongoClient()
    mock_db = mock_client["fastapi_db"]
    mock_collection = mock_db["users"]

    # THIS NOW WORKS because crud reads from db dynamically
    monkeypatch.setattr(db, "user_collection", mock_collection)

    mock_collection.delete_many({})

    client = TestClient(app)
    yield client
