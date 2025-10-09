from pymongo import MongoClient
import datetime
# ✅ تم الإصلاح: لقد قمنا باستيراد ADMIN_CHAT_ID هنا
from config import MONGO_URI, ADMIN_CHAT_ID

# (لا تغييرات في بقية الملف، فقط السطر أعلاه هو الإضافة)
client = MongoClient(MONGO_URI)
db = client.get_database("HijriBotDB_V2")
settings_collection = db.get_collection("BotSettings")
users_collection = db.get_collection("Users")
forwarded_links_collection = db.get_collection("ForwardedLinks")
content_library_collection = db.get_collection("ContentLibrary") # For future use if needed

start_time = datetime.datetime.now()
print("✅ Successfully connected to the fully upgraded cloud database!")

# --- Settings Functions ---
async def get_setting(key: str, default=None):
    doc = await settings_collection.find_one({"_id": "main_bot_config"})
    if not doc:
        return default
    # Support for nested keys like "ui_config.date_button_label"
    keys = key.split('.')
    value = doc
    try:
        for k in keys:
            value = value[k]
        return value
    except KeyError:
        return default

async def update_setting(key: str, value):
    await settings_collection.update_one(
        {"_id": "main_bot_config"},
        {"$set": {key: value}},
        upsert=True
    )

async def update_custom_text(text_key: str, new_text: str):
    await update_setting(f"custom_texts.{text_key}", new_text)

# --- User Functions ---
async def add_user(user_id: int, full_name: str, username: str):
    await users_collection.update_one(
        {"_id": user_id},
        {"$set": {
            "full_name": full_name,
            "username": username,
            "last_seen": datetime.datetime.utcnow(),
            "is_banned": False # Ensure new users are not banned
        }},
        upsert=True
    )

async def is_user_banned(user_id: int) -> bool:
    user = await users_collection.find_one({"_id": user_id})
    return user.get("is_banned", False) if user else False

# --- Forwarded Links ---
async def save_forwarded_link(admin_msg_id: int, user_id: int, user_msg_id: int):
    await forwarded_links_collection.insert_one({
        "_id": admin_msg_id,
        "user_id": user_id,
        "original_message_id": user_msg_id,
        "timestamp": datetime.datetime.utcnow()
    })

async def get_forwarded_link(admin_msg_id: int):
    return await forwarded_links_collection.find_one({"_id": admin_msg_id})

# --- Content Library ---
async def get_all_reminders() -> list:
    reminders_doc = await settings_collection.find_one({"_id": "main_bot_config"}, {"reminders": 1})
    return reminders_doc.get("reminders", []) if reminders_doc else []

async def delete_reminder(reminder_text: str):
    await settings_collection.update_one(
        {"_id": "main_bot_config"},
        {"$pull": {"reminders": reminder_text}}
    )

async def add_reminder(reminder_text: str):
    await settings_collection.update_one(
        {"_id": "main_bot_config"},
        {"$push": {"reminders": reminder_text}},
        upsert=True
    )
    
async def bulk_add_reminders(reminders: list):
    await settings_collection.update_one(
        {"_id": "main_bot_config"},
        {"$push": {"reminders": {"$each": reminders}}},
        upsert=True
    )
    
async def delete_dynamic_reply(keyword: str):
    result = await settings_collection.update_one(
        {"_id": "main_bot_config"},
        {"$unset": {f"dynamic_replies.{keyword}": ""}}
    )
    return result.modified_count > 0

async def add_dynamic_reply(keyword: str, content: str):
    await update_setting(f"dynamic_replies.{keyword}", content)
    
async def bulk_add_dynamic_replies(replies: list[dict]):
    update_ops = {f"dynamic_replies.{item['keyword']}": item['content'] for item in replies}
    await settings_collection.update_one(
        {"_id": "main_bot_config"},
        {"$set": update_ops},
        upsert=True
    )
    
async def get_all_channel_messages() -> list:
    doc = await settings_collection.find_one({"_id": "main_bot_config"}, {"channel_messages": 1})
    return doc.get("channel_messages", []) if doc else []

# --- Database Stats ---
async def get_db_stats():
    try:
        await client.admin.command('ping')
        is_connected = True
    except:
        is_connected = False
        
    reminders_count = len(await get_all_reminders())
    
    dyn_replies_doc = await settings_collection.find_one({"_id": "main_bot_config"}, {"dynamic_replies": 1})
    dyn_replies_count = len(dyn_replies_doc.get("dynamic_replies", {})) if dyn_replies_doc else 0

    return {
        "ok": is_connected,
        "users_count": await users_collection.count_documents({}),
        "reminders_count": reminders_count,
        "dyn_replies_count": dyn_replies_count,
    }
