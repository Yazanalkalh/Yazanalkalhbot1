from pymongo import MongoClient
from config import MONGO_URI

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("HijriBotDB")
    collection = db.get_collection("BotData")
    print("✅ Successfully connected to the cloud database!")
except Exception as e:
    print(f"❌ DATABASE CONNECTION FAILED: {e}")
    exit(1)

def load_db_data():
    """Loads data from MongoDB"""
    data_doc = collection.find_one({"_id": "main_bot_config"})
    return data_doc if data_doc else {}

def save_db_data(data):
    """Saves data to MongoDB"""
    try:
        collection.find_one_and_update(
            {"_id": "main_bot_config"},
            {"$set": data},
            upsert=True
        )
    except Exception as e:
        print(f"DB SAVE ERROR: {e}")
