import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not set")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
user_collection = db[COLLECTION_NAME]
