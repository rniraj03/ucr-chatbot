# database.py
from pymongo import MongoClient
from uuid import uuid4
from datetime import datetime
import os

# Connect to local MongoDB (same URI from MongoDB Compass)
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))

db = client["ai_tutor"]
conversations = db["conversations"]  # replaces "messages" collection

# Temporary default single user
DEFAULT_USER_ID = "anonymous"

def start_conversation(title=None, user_id: str = DEFAULT_USER_ID):
    """Create a new conversation thread for this user."""
    thread_id = str(uuid4())
    conversation = {
        "thread_id": thread_id,
        "user_id": user_id,
        "title": title or f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
        "messages": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    conversations.insert_one(conversation)
    return thread_id

def log_message(role: str, text: str, thread_id: str, user_id: str = DEFAULT_USER_ID):
    """Add one message (user or model) to the correct conversation."""
    conversations.update_one(
        {"thread_id": thread_id, "user_id": user_id},
        {
            "$push": {
                "messages": {
                    "role": role,
                    "text": text,
                    "timestamp": datetime.utcnow()
                }
            },
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

def get_conversation(thread_id: str, user_id: str = DEFAULT_USER_ID):
    """Get the full chat history for one conversation."""
    return conversations.find_one({"thread_id": thread_id, "user_id": user_id}, {"_id": 0})

def list_conversations(user_id: str = DEFAULT_USER_ID):
    """List all conversation threads for this user."""
    return list(
        conversations.find(
            {"user_id": user_id},
            {"_id": 0, "thread_id": 1, "title": 1, "updated_at": 1}
        ).sort("updated_at", -1)
    )

def delete_conversation(thread_id: str, user_id: str = DEFAULT_USER_ID):
    """Optional helper — delete a thread."""
    conversations.delete_one({"thread_id": thread_id, "user_id": user_id})
