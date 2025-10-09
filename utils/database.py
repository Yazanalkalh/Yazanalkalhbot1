# ✅ تم الإصلاح: استيراد المترجم الصحيح motor
from motor.motor_asyncio import AsyncIOMotorClient
import datetime
from config import MONGO_URI, ADMIN_CHAT_ID

# ✅ تم الإصلاح: استخدام AsyncIOMotorClient بدلاً من MongoClient
client = AsyncIOMotorClient(MONGO_URI)
db = client.get_database("HijriBotDB_V2")

settings_collection = db.get_collection("BotSettings")
users_collection = db.get_collection("Users")
forwarded_links_collection = db.get_collection("ForwardedLinks")
content_library_collection = db.get_collection("ContentLibrary")
scheduled_posts_collection = db.get_collection("ScheduledPosts")
channels_collection = db.get_collection("Channels")

start_time = datetime.datetime.now()
print("✅ Successfully connected to the ASYNC cloud database!")

# --- Settings Functions ---
# كل الدوال الآن تستخدم await بشكل صحيح مع motor
async def get_setting(key: str, default=None):
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

# --- Channel Management ---
async def add_pending_channel(chat_id: int, title: str):
    await channels_collection.update_one(
        {"_id": chat_id},
        {"$set": {"title": title, "status": "pending", "added_at": datetime.datetime.utcnow()}},
        upsert=True
    )

async def approve_channel(chat_id: int):
    await channels_collection.update_one({"_id": chat_id}, {"$set": {"status": "approved"}})

async def reject_channel(chat_id: int):
    await channels_collection.delete_one({"_id": chat_id})

async def get_pending_channels():
    cursor = channels_collection.find({"status": "pending"})
    return await cursor.to_list(length=100) # motor requires this syntax for find()

async def get_approved_channels():
    cursor = channels_collection.find({"status": "approved"})
    return await cursor.to_list(length=100)

# --- Database Stats ---
async def get_db_stats():
    try:
        await client.admin.command('ping')
        is_connected = True
    except:
        is_connected = False
    return {"ok": is_connected, "users_count": await users_collection.count_documents({})}

# ... (يمكن إضافة بقية الدوال المساعدة هنا إذا احتجنا إليها لاحقًا)
