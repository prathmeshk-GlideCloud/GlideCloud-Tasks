def user_serializer(user) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "age": user["age"],
        "created_at": user["created_at"],
        "updated_at": user.get("updated_at")
    }
