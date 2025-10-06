from pymongo import MongoClient, DESCENDING
from config import MONGO_URI
import hashlib
import datetime

# This is the fully upgraded "Warehouse Manager".
# It now handles settings, content library, channels, users, and stats.

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("HijriBotDB_V2")
    
    settings_collection = db.get_collection("BotSettings")
    content_library_collection = db.get_collection("ContentLibrary")
    scheduled_posts_collection = db.get_collection("ScheduledPosts")
    # NEW Collections for advanced features
    channels_collection = db.get_collection("Channels")
    users_collection = db.get_collection("Users")

    print("✅ Successfully connected to the fully upgraded cloud database!")
except Exception as e:
    print(f"❌ DATABASE CONNECTION FAILED: {e}")
    exit(1)

# --- Settings & User Functions ---
def load_db_data():
    """Loads general bot settings."""
    data_doc = settings_collection.find_one({"_id": "main_bot_config"})
    return data_doc if data_doc else {}

def save_db_data(data):
    """Saves general bot settings."""
    try:
        settings_collection.find_one_and_update(
            {"_id": "main_bot_config"}, {"$set": data}, upsert=True
        )
    except Exception as e:
        print(f"DB SETTINGS SAVE ERROR: {e}")

def add_user(user_id: int, full_name: str, username: str):
    """Adds or updates a user in the database."""
    users_collection.update_one(
        {"_id": user_id},
        {"$set": {
            "full_name": full_name,
            "username": username,
            "last_seen": datetime.datetime.utcnow()
        }},
        upsert=True
    )

# --- Content Library Functions ---
def add_content_to_library(content_type: str, content_value: str) -> str:
    content_hash = hashlib.sha256(content_value.encode()).hexdigest()
    if not content_library_collection.find_one({"_id": content_hash}):
        content_library_collection.insert_one({
            "_id": content_hash, "type": content_type,
            "value": content_value, "added_at": datetime.datetime.utcnow()
        })
    return content_hash

def get_content_from_library(content_id: str):
    return content_library_collection.find_one({"_id": content_id})

def get_all_library_content(limit=20):
    """Retrieves the most recent items from the library."""
    return list(content_library_collection.find().sort("added_at", DESCENDING).limit(limit))

def delete_content_by_id(content_id: str):
    """Deletes a specific item from the content library."""
    content_library_collection.delete_one({"_id": content_id})

# --- Scheduled Posts Functions ---
def add_scheduled_post(content_id: str, channel_id: str, send_at_utc: datetime.datetime):
    scheduled_posts_collection.insert_one({
        "content_id": content_id, "channel_id": str(channel_id),
        "send_at": send_at_utc, "sent": False
    })

def get_due_scheduled_posts() -> list:
    now_utc = datetime.datetime.utcnow()
    return list(scheduled_posts_collection.find({
        "send_at": {"$lte": now_utc}, "sent": False
    }))

def mark_post_as_sent(post_object_id):
    scheduled_posts_collection.update_one(
        {"_id": post_object_id}, {"$set": {"sent": True}}
    )

# --- NEW: Channel/Group Management Functions ---
def add_pending_channel(chat_id: int, title: str):
    """Adds a new channel/group to the pending list for admin approval."""
    # Use update_one with upsert to avoid duplicate errors if the bot is re-added
    channels_collection.update_one(
        {"_id": chat_id},
        {"$set": {
            "title": title,
            "status": "pending",
            "added_at": datetime.datetime.utcnow()
        }},
        upsert=True
    )

def approve_channel(chat_id: int):
    """Approves a pending channel."""
    channels_collection.update_one({"_id": chat_id}, {"$set": {"status": "approved"}})

def reject_channel(chat_id: int):
    """Rejects (deletes) a pending channel request."""
    channels_collection.delete_one({"_id": chat_id})

def get_pending_channels():
    """Gets a list of all channels awaiting approval."""
    return list(channels_collection.find({"status": "pending"}))

def get_approved_channels():
    """Gets a list of all approved channels for broadcasting."""
    return list(channels_collection.find({"status": "approved"}))

# --- NEW: Stats & System Status Functions ---
def get_db_stats():
    """Gathers various statistics from the database."""
    try:
        # Pinging the server is a good way to check connection.
        db.command('ping')
        is_connected = True
    except:
        is_connected = False
        
    return {
        "ok": is_connected,
        "library_count": content_library_collection.count_documents({}),
        "scheduled_count": scheduled_posts_collection.count_documents({"sent": False}),
        "users_count": users_collection.count_documents({})
    }
