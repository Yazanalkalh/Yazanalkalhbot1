from pymongo import MongoClient
from config import MONGO_URI
import hashlib
import datetime

# This file is now upgraded to be a "Warehouse Manager".
# It handles saving general settings, managing a content library, and scheduling posts.

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("HijriBotDB_V2") # Using a new DB version for safety
    
    # Collection for general bot data (like settings, users, etc.)
    settings_collection = db.get_collection("BotSettings")
    
    # NEW: Collection for the Content Library. Each piece of content is stored only once.
    content_library_collection = db.get_collection("ContentLibrary")
    
    # NEW: Collection for scheduled posts. Only stores references to the content library.
    scheduled_posts_collection = db.get_collection("ScheduledPosts")

    print("✅ Successfully connected to the upgraded cloud database!")
except Exception as e:
    print(f"❌ DATABASE CONNECTION FAILED: {e}")
    exit(1)

# --- Old Functions (Still work for general settings) ---

def load_db_data():
    """Loads general bot data (settings, users, etc.)"""
    data_doc = settings_collection.find_one({"_id": "main_bot_config"})
    return data_doc if data_doc else {}

def save_db_data(data):
    """Saves general bot data (settings, users, etc.)"""
    try:
        settings_collection.find_one_and_update(
            {"_id": "main_bot_config"},
            {"$set": data},
            upsert=True
        )
    except Exception as e:
        print(f"DB SETTINGS SAVE ERROR: {e}")


# --- NEW: Content Library Functions ---

def add_content_to_library(content_type: str, content_value: str) -> str:
    """
    Adds a piece of content to the library if it doesn't exist, and returns its unique ID.
    'content_value' is the text itself or the file_id for stickers/photos.
    """
    # Create a unique hash to represent the content, preventing duplicates.
    content_hash = hashlib.sha256(content_value.encode()).hexdigest()

    # Check if this content already exists in the library
    existing_content = content_library_collection.find_one({"_id": content_hash})

    if existing_content:
        # If it exists, just return its ID
        return existing_content["_id"]
    else:
        # If it's new, add it to the library and then return its ID
        new_content = {
            "_id": content_hash,
            "type": content_type,
            "value": content_value,
            "added_at": datetime.datetime.utcnow()
        }
        content_library_collection.insert_one(new_content)
        return content_hash

def get_content_from_library(content_id: str) -> dict or None:
    """Retrieves a piece of content from the library by its ID."""
    return content_library_collection.find_one({"_id": content_id})


# --- NEW: Scheduled Posts Functions ---

def add_scheduled_post(content_id: str, channel_id: str, send_at_utc: datetime.datetime):
    """Schedules a post by adding a reference to the content library."""
    new_post = {
        "content_id": content_id,
        "channel_id": channel_id,
        "send_at": send_at_utc,
        "sent": False # To track if it has been sent
    }
    scheduled_posts_collection.insert_one(new_post)

def get_due_scheduled_posts() -> list:
    """Gets all scheduled posts that are due to be sent."""
    now_utc = datetime.datetime.utcnow()
    # Find all posts where send_at is less than or equal to now, and it hasn't been sent yet.
    due_posts_cursor = scheduled_posts_collection.find({
        "send_at": {"$lte": now_utc},
        "sent": False
    })
    return list(due_posts_cursor)

def mark_post_as_sent(post_object_id):
    """Marks a post as 'sent' so it doesn't get sent again."""
    scheduled_posts_collection.update_one(
        {"_id": post_object_id},
        {"$set": {"sent": True}}
    )
