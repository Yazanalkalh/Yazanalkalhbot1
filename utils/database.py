from pymongo import MongoClient, DESCENDING
from config import MONGO_URI
import hashlib
import datetime

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("HijriBotDB_V2")
    
    settings_collection = db.get_collection("BotSettings")
    content_library_collection = db.get_collection("ContentLibrary")
    scheduled_posts_collection = db.get_collection("ScheduledPosts")
    channels_collection = db.get_collection("Channels")
    users_collection = db.get_collection("Users")

    print("✅ Successfully connected to the fully upgraded cloud database!")
except Exception as e:
    print(f"❌ DATABASE CONNECTION FAILED: {e}")
    exit(1)

# --- Settings Functions ---

def get_all_settings():
    """
    Loads the entire settings document. 
    Should only be used on startup if needed, not for regular operations.
    """
    settings_doc = settings_collection.find_one({"_id": "main_bot_config"})
    return settings_doc if settings_doc else {}

def get_setting(setting_name: str, default_value=None):
    """
    ✅ دالة جديدة: لجلب قيمة إعداد واحد بشكل فعال وسريع.
    
    Example: get_setting("welcome_message", "Default Welcome!")
    """
    settings_doc = settings_collection.find_one({"_id": "main_bot_config"}, {setting_name: 1})
    if settings_doc and setting_name in settings_doc:
        return settings_doc[setting_name]
    return default_value

def update_setting(setting_name: str, value):
    """
    ✅ دالة جديدة: لتحديث قيمة إعداد واحد بشكل آمن.
    """
    try:
        settings_collection.update_one(
            {"_id": "main_bot_config"},
            {"$set": {setting_name: value}},
            upsert=True
        )
    except Exception as e:
        print(f"DB SETTING UPDATE ERROR for '{setting_name}': {e}")


# --- User Functions ---
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

# ... (بقية الدوال في ملفك تبقى كما هي بدون تغيير) ...
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
    return list(content_library_collection.find().sort("added_at", DESCENDING).limit(limit))

def delete_content_by_id(content_id: str):
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

# --- Channel/Group Management Functions ---
def add_pending_channel(chat_id: int, title: str):
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
    channels_collection.update_one({"_id": chat_id}, {"$set": {"status": "approved"}})

def reject_channel(chat_id: int):
    channels_collection.delete_one({"_id": chat_id})

def get_pending_channels():
    return list(channels_collection.find({"status": "pending"}))

def get_approved_channels():
    return list(channels_collection.find({"status": "approved"}))

# --- Stats & System Status Functions ---
def get_db_stats():
    """Gathers various statistics from the database."""
    try:
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
