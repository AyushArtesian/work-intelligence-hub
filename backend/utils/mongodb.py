from db import mongodb as mongodb_core

mongo_client = None
mongo_db = None


def init_mongo():
    global mongo_client, mongo_db
    mongo_db = mongodb_core.init_mongo()
    mongo_client = mongodb_core.mongo_client
    return mongo_db


def get_db():
    global mongo_client, mongo_db
    mongo_db = mongodb_core.get_db()
    mongo_client = mongodb_core.mongo_client
    return mongo_db
