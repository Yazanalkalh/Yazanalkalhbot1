from pymongo import MongoClient
from config import MONGO_URI

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("HijriBotDB")
    collection = db.get_collection("BotData")
    print("✅ تم الاتصال بقاعدة البيانات السحابية بنجاح!")
except Exception as e:
    print(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
    exit(1)

def load_data_from_db():
    """تحميل البيانات من قاعدة بيانات MongoDB"""
    data_doc = collection.find_one({"_id": "main_bot_config"})
    default_data = {
        "auto_replies": {}, "daily_reminders": [], "channel_messages": [],
        "banned_users": [], "users": [], "channel_id": "", "allow_media": False,
        "media_reject_message": "❌ **عذراً، استقبال الوسائط معطل حالياً.**\nيُسمح بالرسائل النصية فقط.",
        "welcome_message": "", "reply_message": "",
        "schedule_interval_seconds": 86400  # 24 hours
    }
    if data_doc:
        default_data.update(data_doc)
    return default_data

def save_data_to_db(data):
    """حفظ البيانات في قاعدة بيانات MongoDB"""
    try:
        collection.update_one(
            {"_id": "main_bot_config"},
            {"$set": data},
            upsert=True
        )
    except Exception as e:
        print(f"خطأ في حفظ البيانات في MongoDB: {e}")
