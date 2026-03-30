#!/usr/bin/env python
"""
Cleanup script to fix documents with null source/message_id in MongoDB.
This should be run once after updating Phase 2 code.
"""
import sys
from pymongo import MongoClient
from utils.settings import settings

def cleanup_messages_collection():
    uri = str(settings.MONGODB_URI)
    db_name = getattr(settings, "DATABASE_NAME", "ai_work_assistant") or "ai_work_assistant"
    
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        db = client[db_name]
        messages = db["messages"]
        
        print(f"Connected to {db_name}")
        
        # Count documents with null source and message_id
        bad_docs = messages.count_documents({"source": None, "message_id": None})
        print(f"Found {bad_docs} documents with null source and message_id")
        
        if bad_docs > 0:
            print("Deleting documents with null source and message_id...")
            result = messages.delete_many({"source": None, "message_id": None})
            print(f"Deleted {result.deleted_count} documents")
        
        # Try to drop the existing problematic index
        try:
            messages.drop_index("uniq_user_source_message")
            print("Dropped existing uniq_user_source_message index")
        except Exception as e:
            print(f"No index to drop or error: {e}")
        
        print("Cleanup complete!")
        client.close()
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    cleanup_messages_collection()
