from pymongo import MongoClient
import datetime
from config import MONGO_URI, ADMIN_CHAT_ID

# نعود إلى MongoClient الأصلي والمستقر
client = MongoClient(MONGO_URI)
db = client.get_database("HijriBotDB_V2")

settings_collection = db.get_collection("BotSettings")
users_collection = db.get_collection("Users")
forwarded_links_collection = db.get_collection("ForwardedLinks")
channels_collection = db.get_collection("Channels")
# يمكن إضافة بقية المجموعات هنا إذا احتجت إليها

start_time = datetime.datetime.now()
print("✅ Successfully connected to the SYNC cloud database!")

# --- Settings Functions ---
# كل الدوال الآن متزامنة (لا يوجد async/await)
def get_setting(key: str, default=None):
    doc = settings_collection.find_one({"_id": "main_bot_config"})
    if not doc: return default
    keys = key.split('.'); value = doc
    try:
        for k in keys: value = value[k]
        return value
    except (KeyError, TypeError):
        return default

def update_setting(key: str, value):
    settings_collection.update_one({"_id": "main_bot_config"}, {"$set": {key: value}}, upsert=True)

# --- User Functions ---
def add_user(user_id: int, full_name: str, username: str):
    users_collection.update_one(
        {"_id": user_id},
        {"$set": {"full_name": full_name, "username": username, "last_seen": datetime.datetime.utcnow(), "is_banned": False}},
        upsert=True
    )

def is_user_banned(user_id: int) -> bool:
    user = users_collection.find_one({"_id": user_id})
    return user.get("is_banned", False) if user else False

# --- Forwarded Links ---
def save_forwarded_link(admin_msg_id: int, user_id: int, user_msg_id: int):
    forwarded_links_collection.insert_one({"_id": admin_msg_id, "user_id": user_id, "original_message_id": user_msg_id})

def get_forwarded_link(admin_msg_id: int):
    return forwarded_links_collection.find_one({"_id": admin_msg_id})

# --- Channel Management ---
def add_pending_channel(chat_id: int, title: str):
    channels_collection.update_one({"_id": chat_id}, {"$set": {"title": title, "status": "pending"}}, upsert=True)

def approve_channel(chat_id: int):
    channels_collection.update_one({"_id": chat_id}, {"$set": {"status": "approved"}})

def reject_channel(chat_id: int):
    channels_collection.delete_one({"_id": chat_id})

def get_pending_channels():
    return list(channels_collection.find({"status": "pending"}))

def get_approved_channels():
    return list(channels_collection.find({"status": "approved"}))

# --- Reminders & Messages ---
def get_all_reminders() -> list:
    doc = settings_collection.find_one({"_id": "main_bot_config"}, {"reminders": 1})
    return doc.get("reminders", []) if doc else []

def get_all_channel_messages() -> list:
    doc = settings_collection.find_one({"_id": "main_bot_config"}, {"channel_messages": 1})
    return doc.get("channel_messages", []) if doc else []

# --- Database Stats ---
def get_db_stats():
    try:
        client.admin.command('ping')
        is_connected = True
    except:
        is_connected = False
    return {"ok": is_connected, "users_count": users_collection.count_documents({})}
