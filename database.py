from pymongo import MongoClient
from config import MONGO_URI

# --- Setup for the cloud database (MongoDB) ---
try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("HijriBotDB")       # Database name
    collection = db.get_collection("BotData")    # Collection (table) name
    print("✅ Successfully connected to the cloud database!")
except Exception as e:
    print(f"❌ Failed to connect to the database: {e}")
    exit(1)

def load_data():
    """Loads data from the MongoDB database."""
    data_doc = collection.find_one({"_id": "main_bot_config"})
    
    # Default data structure to ensure no errors occur if keys are missing
    default_data = {
        "auto_replies": {}, "daily_reminders": [], "channel_messages": [],
        "banned_users": [], "users": [], "channel_id": "", "allow_media": False,
        "media_reject_message": "❌ يُسمح بالرسائل النصية فقط. يرجى إرسال النص فقط.",
        "rejected_media_count": 0, "welcome_message": "", "reply_message": "",
        "schedule_interval_seconds": 86400
    }

    if data_doc:
        data_doc.pop("_id", None) # Remove the internal MongoDB ID
        # Merge loaded data with defaults to ensure all keys are present
        default_data.update(data_doc)
    
    return default_data

def save_data(data):
    """Saves data to the MongoDB database."""
    try:
        # This command updates the document if it exists, or creates it if it doesn't
        collection.find_one_and_update(
            {"_id": "main_bot_config"},
            {"$set": data},
            upsert=True
        )
    except Exception as e:
        print(f"Error saving data to MongoDB: {e}")


