from pymongo import MongoClient
from config import MONGO_URI, ADMIN_CHAT_ID
import datetime

# --- Database Connection ---
try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("HijriBotDB_VIP") # Using a new DB name for a fresh start
    
    settings_collection = db.get_collection("Settings")
    users_collection = db.get_collection("Users")
    content_collection = db.get_collection("Content") # For reminders, channel posts, etc.
    forwarded_links_collection = db.get_collection("ForwardedLinks")

    # A single document to hold all bot settings
    settings_collection.update_one({"_id": "bot_config"}, {"$setOnInsert": {}}, upsert=True)
    
    print("✅ Successfully connected to the SYNC cloud database!")
except Exception as e:
    print(f"❌ DATABASE CONNECTION FAILED: {e}")
    exit(1)

# To calculate uptime
start_time = datetime.datetime.now()

# --- Settings Functions ---
def get_setting(key, default=None):
    """Gets a specific setting value from the database."""
    config = settings_collection.find_one({"_id": "bot_config"})
    # Use dot notation to get nested keys (e.g., 'ui.welcome_message')
    keys = key.split('.')
    value = config
    try:
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        return default

def update_setting(key, value):
    """Updates a specific setting value in the database."""
    settings_collection.update_one({"_id": "bot_config"}, {"$set": {key: value}}, upsert=True)

# --- User Management ---
def add_user(user_id, full_name, username):
    users_collection.update_one(
        {"_id": user_id},
        {"$set": {
            "full_name": full_name,
            "username": username,
            "last_seen": datetime.datetime.now()
        }, "$setOnInsert": {"is_banned": False, "join_date": datetime.datetime.now()}},
        upsert=True
    )

def is_user_banned(user_id):
    user = users_collection.find_one({"_id": user_id})
    return user.get("is_banned", False) if user else False

def ban_user(user_id):
    users_collection.update_one({"_id": user_id}, {"$set": {"is_banned": True}}, upsert=True)

def unban_user(user_id):
    users_collection.update_one({"_id": user_id}, {"$set": {"is_banned": False}})

def get_all_user_ids():
    return [user["_id"] for user in users_collection.find({}, {"_id": 1})]

# --- Content Management (Reminders, etc.) ---
def add_reminder(text):
    content_collection.update_one(
        {"_id": "reminders"},
        {"$addToSet": {"items": text}}, # $addToSet prevents duplicates
        upsert=True
    )

def get_all_reminders():
    doc = content_collection.find_one({"_id": "reminders"})
    return doc.get("items", []) if doc else []

def get_random_reminder():
    import random
    reminders = get_all_reminders()
    return random.choice(reminders) if reminders else "لا توجد تذكيرات حاليًا."

# --- Forwarded Message Links ---
def save_forwarded_link(admin_msg_id, user_id, user_msg_id):
    forwarded_links_collection.insert_one({
        "_id": admin_msg_id,
        "user_id": user_id,
        "original_message_id": user_msg_id,
        "timestamp": datetime.datetime.now()
    })

def get_forwarded_link(admin_msg_id):
    return forwarded_links_collection.find_one({"_id": admin_msg_id})

# --- Statistics ---
def get_db_stats():
    return {
        "users_count": users_collection.count_documents({}),
        "banned_count": users_collection.count_documents({"is_banned": True}),
        "reminders_count": len(get_all_reminders()),
    }
