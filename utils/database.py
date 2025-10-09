from pymongo import MongoClient
import datetime
from config import MONGO_URI, ADMIN_CHAT_ID

client = MongoClient(MONGO_URI)
db = client.get_database("HijriBotDB_V2")

# ✅ تم الإصلاح: إعادة تعريف كل المجموعات (Collections) المطلوبة
settings_collection = db.get_collection("BotSettings")
users_collection = db.get_collection("Users")
forwarded_links_collection = db.get_collection("ForwardedLinks")
content_library_collection = db.get_collection("ContentLibrary")
scheduled_posts_collection = db.get_collection("ScheduledPosts")
channels_collection = db.get_collection("Channels") # <-- هذه كانت مفقودة

start_time = datetime.datetime.now()
print("✅ Successfully connected to the fully upgraded cloud database!")

# --- Settings Functions ---
async def get_setting(key: str, default=None):
    # This function uses find_one which is already async with motor
    doc = await settings_collection.find_one({"_id": "main_bot_config"})
    if not doc: return default
    keys = key.split('.'); value = doc
    try:
        for k in keys: value = value[k]
        return value
    except KeyError: return default

async def update_setting(key: str, value):
    await settings_collection.update_one({"_id": "main_bot_config"}, {"$set": {key: value}}, upsert=True)

# --- User Functions ---
async def add_user(user_id: int, full_name: str, username: str):
    await users_collection.update_one(
        {"_id": user_id},
        {"$set": {"full_name": full_name, "username": username, "last_seen": datetime.datetime.utcnow(), "is_banned": False}},
        upsert=True
    )

async def is_user_banned(user_id: int) -> bool:
    user = await users_collection.find_one({"_id": user_id})
    return user.get("is_banned", False) if user else False

# --- Forwarded Links ---
async def save_forwarded_link(admin_msg_id: int, user_id: int, user_msg_id: int):
    await forwarded_links_collection.insert_one({"_id": admin_msg_id, "user_id": user_id, "original_message_id": user_msg_id})

async def get_forwarded_link(admin_msg_id: int):
    return await forwarded_links_collection.find_one({"_id": admin_msg_id})

# --- Content, Reminders, Replies ---
async def get_all_reminders() -> list:
    doc = await settings_collection.find_one({"_id": "main_bot_config"}, {"reminders": 1})
    return doc.get("reminders", []) if doc else []
    
async def get_all_channel_messages() -> list:
    doc = await settings_collection.find_one({"_id": "main_bot_config"}, {"channel_messages": 1})
    return doc.get("channel_messages", []) if doc else []

# ... (Add other content functions if needed, like add_reminder, delete_reminder, etc.)

# ✅ --- تم الإصلاح: إعادة إضافة كل دوال إدارة القنوات المفقودة ---
def add_pending_channel(chat_id: int, title: str):
    """Adds a new channel/group to the pending list for admin approval."""
    channels_collection.update_one(
        {"_id": chat_id},
        {"$set": {"title": title, "status": "pending", "added_at": datetime.datetime.utcnow()}},
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
# --------------------------------------------------------------------

# --- Database Stats ---
async def get_db_stats():
    # ... (rest of the file is correct)
    try:
        await client.admin.command('ping')
        is_connected = True
    except:
        is_connected = False
    return {"ok": is_connected, "users_count": await users_collection.count_documents({})}
