from pymongo import MongoClient, DESCENDING
from config import MONGO_URI
import hashlib
import datetime

# هذا الملف هو النسخة الكاملة والمحدثة لمدير قاعدة البيانات
# قم بنسخ هذا الملف بالكامل واستبدال الملف القديم لديك

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("HijriBotDB_V2")
    
    settings_collection = db.get_collection("BotSettings")
    users_collection = db.get_collection("Users")
    forward_links_collection = db.get_collection("ForwardLinks")
    content_library_collection = db.get_collection("ContentLibrary")
    scheduled_posts_collection = db.get_collection("ScheduledPosts")
    channels_collection = db.get_collection("Channels")

    print("✅ Successfully connected to the fully upgraded cloud database!")
except Exception as e:
    print(f"❌ DATABASE CONNECTION FAILED: {e}")
    exit(1)

# --- دوال الإعدادات ---
def get_all_settings():
    settings_doc = settings_collection.find_one({"_id": "main_bot_config"})
    return settings_doc if settings_doc else {}

def get_setting(setting_name: str, default_value=None):
    settings_doc = settings_collection.find_one({"_id": "main_bot_config"}, {setting_name: 1})
    if settings_doc and setting_name in settings_doc:
        return settings_doc[setting_name]
    return default_value

def update_setting(setting_name: str, value):
    try:
        settings_collection.update_one(
            {"_id": "main_bot_config"}, {"$set": {setting_name: value}}, upsert=True
        )
    except Exception as e:
        print(f"DB SETTING UPDATE ERROR for '{setting_name}': {e}")

# --- دوال المستخدمين ---
def add_user(user_id: int, full_name: str, username: str):
    users_collection.update_one(
        {"_id": user_id},
        {
            "$set": {"full_name": full_name, "username": username, "last_seen": datetime.datetime.utcnow()},
            "$setOnInsert": {"is_banned": False, "last_message_fingerprint": None}
        },
        upsert=True
    )

def is_user_banned(user_id: int) -> bool:
    user = users_collection.find_one({"_id": user_id}, {"is_banned": 1})
    return user.get("is_banned", False) if user else False

def get_user_last_fingerprint(user_id: int) -> str or None:
    user = users_collection.find_one({"_id": user_id}, {"last_message_fingerprint": 1})
    return user.get("last_message_fingerprint") if user else None

def update_user_last_fingerprint(user_id: int, fingerprint: str):
    users_collection.update_one({"_id": user_id}, {"$set": {"last_message_fingerprint": fingerprint}})

# --- دوال الردود والتذكيرات والنصوص ---
def get_dynamic_reply(text: str) -> str or None:
    if not text: return None
    reply_data = settings_collection.find_one({"_id": "main_bot_config"}, {f"dynamic_replies.{text}": 1})
    if reply_data and "dynamic_replies" in reply_data:
        return reply_data["dynamic_replies"].get(text)
    return None

def add_or_update_dynamic_reply(keyword: str, content: str):
    settings_collection.update_one({"_id": "main_bot_config"}, {"$set": {f"dynamic_replies.{keyword}": content}}, upsert=True)

def delete_dynamic_reply(keyword: str) -> bool:
    result = settings_collection.update_one({"_id": "main_bot_config"}, {"$unset": {f"dynamic_replies.{keyword}": ""}})
    return result.modified_count > 0

def get_all_dynamic_replies() -> dict:
    return get_setting("dynamic_replies", {})

def add_reminder(reminder_text: str):
    settings_collection.update_one({"_id": "main_bot_config"}, {"$addToSet": {"reminders": reminder_text}})

def delete_reminder(reminder_text: str) -> bool:
    result = settings_collection.update_one({"_id": "main_bot_config"}, {"$pull": {"reminders": reminder_text}})
    return result.modified_count > 0

def get_all_reminders() -> list:
    return get_setting("reminders", [])

def update_custom_text(key: str, text: str):
    settings_collection.update_one({"_id": "main_bot_config"}, {"$set": {f"custom_texts.{key}": text}}, upsert=True)
    
# --- دوال روابط الرسائل المحولة ---
def log_forward_link(admin_message_id: int, user_id: int, original_message_id: int):
    forward_links_collection.insert_one({
        "_id": admin_message_id, "user_id": user_id,
        "original_message_id": original_message_id, "created_at": datetime.datetime.utcnow()
    })

def get_forward_link(admin_message_id: int):
    return forward_links_collection.find_one({"_id": admin_message_id})

def delete_forward_link(admin_message_id: int):
    forward_links_collection.delete_one({"_id": admin_message_id})

# --- دوال الإحصائيات (تبقى كما هي) ---
def get_db_stats():
    try: db.command('ping'); is_connected = True
    except: is_connected = False
    return {
        "ok": is_connected,
        "library_count": content_library_collection.count_documents({}),
        "scheduled_count": scheduled_posts_collection.count_documents({"sent": False}),
        "users_count": users_collection.count_documents({})
    }

# --- دوال مكتبة المحتوى ---
def add_content_to_library(content_type: str, content_value: str) -> str:
    content_hash = hashlib.sha256(content_value.encode()).hexdigest()
    if not content_library_collection.find_one({"_id": content_hash}):
        content_library_collection.insert_one({
            "_id": content_hash, "type": content_type,
            "value": content_value, "added_at": datetime.datetime.utcnow()
        })
    return content_hash

def get_all_library_content(limit=20):
    return list(content_library_collection.find().sort("added_at", DESCENDING).limit(limit))

def delete_content_by_id(content_id: str):
    content_library_collection.delete_one({"_id": content_id})

# --- دوال القنوات ---
def add_pending_channel(chat_id: int, title: str):
    channels_collection.update_one(
        {"_id": chat_id}, {"$set": {"title": title, "status": "pending", "added_at": datetime.datetime.utcnow()}}, upsert=True
    )
def approve_channel(chat_id: int):
    channels_collection.update_one({"_id": chat_id}, {"$set": {"status": "approved"}})
def reject_channel(chat_id: int):
    channels_collection.delete_one({"_id": chat_id})
def get_pending_channels():
    return list(channels_collection.find({"status": "pending"}))
def get_approved_channels():
    return list(channels_collection.find({"status": "approved"}))
