import logging
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from utils.settings import settings

logger = logging.getLogger(__name__)

mongo_client: MongoClient | None = None
mongo_db: Database | None = None


def init_mongo() -> Database | None:
    global mongo_client, mongo_db

    if mongo_client is not None and mongo_db is not None:
        return mongo_db

    try:
        mongo_client = MongoClient(str(settings.MONGODB_URI), serverSelectionTimeoutMS=5000)
        mongo_client.admin.command("ping")
        mongo_db = mongo_client[getattr(settings, "DATABASE_NAME", "ai_work_assistant") or "ai_work_assistant"]
        _ensure_collections(mongo_db)
        logger.info("MongoDB initialized")
        return mongo_db
    except Exception as exc:
        logger.warning("MongoDB connection failed: %s", exc)
        mongo_client = None
        mongo_db = None
        return None


def get_db() -> Database | None:
    if mongo_db is None:
        return init_mongo()
    return mongo_db


def get_messages_collection() -> Collection | None:
    db = get_db()
    if db is None:
        return None
    return db["messages"]


def _ensure_collections(db: Database) -> None:
    names = db.list_collection_names()
    if "messages" not in names:
        db.create_collection("messages")

    messages = db["messages"]
    
    # Handle unique index on message_id + user_id + source with graceful error handling
    try:
        messages.create_index(
            [("user_id", 1), ("source", 1), ("message_id", 1)],
            unique=True,
            sparse=True,
            name="uniq_user_source_message",
        )
    except Exception as exc:
        # If index creation fails (e.g., E11000 duplicate key), try to drop and recreate
        if "duplicate key" in str(exc).lower() or "11000" in str(exc):
            try:
                messages.drop_index("uniq_user_source_message")
            except Exception:
                pass
            # Delete documents with null source and message_id to allow index creation
            try:
                messages.delete_many({"source": None, "message_id": None})
            except Exception:
                pass
            # Try again
            try:
                messages.create_index(
                    [("user_id", 1), ("source", 1), ("message_id", 1)],
                    unique=True,
                    sparse=True,
                    name="uniq_user_source_message",
                )
            except Exception as retry_exc:
                logger.warning("Unable to create unique index after cleanup: %s", retry_exc)
        else:
            logger.warning("Failed to create unique index: %s", exc)
    
    # Create regular indexes
    try:
        messages.create_index([("user_id", 1), ("timestamp", -1)], name="idx_user_timestamp")
    except Exception as exc:
        logger.warning("Failed to create user_timestamp index: %s", exc)
    
    try:
        messages.create_index([("chat_id", 1), ("timestamp", -1)], name="idx_chat_timestamp")
    except Exception as exc:
        logger.warning("Failed to create chat_timestamp index: %s", exc)


def health() -> dict[str, Any]:
    if mongo_client is None:
        return {"status": "db_unavailable"}

    try:
        mongo_client.admin.command("ping")
        return {"status": "db_available"}
    except Exception as exc:
        return {"status": "db_unavailable", "error": str(exc)}
