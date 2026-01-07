def test_create_user(test_client):
    response = test_client.post(
        "/users",
        json={"name": "Test User", "age": 25}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Test User"
    assert data["age"] == 25
    assert "id" in data

def test_get_users(test_client):
    test_client.post("/users", json={"name": "User1", "age": 20})
    test_client.post("/users", json={"name": "User2", "age": 30})

    response = test_client.get("/users")

    assert response.status_code == 200
    assert len(response.json()) == 2

def test_get_user_by_id(test_client):
    create_resp = test_client.post(
        "/users",
        json={"name": "Single User", "age": 28}
    )

    user_id = create_resp.json()["id"]

    response = test_client.get(f"/users/{user_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Single User"

def test_update_user(test_client):
    create_resp = test_client.post(
        "/users",
        json={"name": "Old Name", "age": 22}
    )

    user_id = create_resp.json()["id"]

    response = test_client.put(
        f"/users/{user_id}",
        json={"name": "New Name"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "New Name"

def test_delete_user(test_client):
    create_resp = test_client.post(
        "/users",
        json={"name": "Delete Me", "age": 35}
    )

    user_id = create_resp.json()["id"]

    delete_resp = test_client.delete(f"/users/{user_id}")
    assert delete_resp.status_code == 200

    get_resp = test_client.get(f"/users/{user_id}")
    assert get_resp.status_code == 404


