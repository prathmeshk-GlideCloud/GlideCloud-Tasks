from datetime import datetime
from bson import ObjectId
import db
from models import user_serializer


def create_user(user_data: dict):
    user_data["created_at"] = datetime.utcnow()
    user_data["updated_at"] = None

    result = db.user_collection.insert_one(user_data)
    return get_user(str(result.inserted_id))


def get_user(user_id: str):
    user = db.user_collection.find_one({"_id": ObjectId(user_id)})
    return user_serializer(user) if user else None


def get_all_users():
    return [user_serializer(u) for u in db.user_collection.find()]


def update_user(user_id: str, update_data: dict):
    update_data["updated_at"] = datetime.utcnow()

    result = db.user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        return None

    return get_user(user_id)


def delete_user(user_id: str):
    result = db.user_collection.delete_one({"_id": ObjectId(user_id)})
    return result.deleted_count > 0
