from pymongo import MongoClient
from .settings import settings

mongo_client: MongoClient | None = None
mongo_db = None


def init_mongo():
    global mongo_client, mongo_db
    if mongo_client is None:
        uri = str(settings.MONGODB_URI)
        try:
            # use serverSelectionTimeoutMS to fail fast if DNS or network is invalid
            mongo_client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            # attempt a simple operation to validate connection
            mongo_client.admin.command("ping")
            mongo_db = mongo_client[settings.DATABASE_NAME]
        except Exception as exc:
            # fallback: log and avoid raising at startup
            # db access will fail later where needed.
            mongo_client = None
            mongo_db = None
            print("[WARNING] MongoDB connection failed:", exc)
    return mongo_db


def get_db():
    if mongo_db is None:
        return init_mongo()
    return mongo_db
