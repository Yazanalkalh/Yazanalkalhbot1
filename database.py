from pymongo import MongoClient
from config import MONGO_URI

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("HijriBotDB")
    collection = db.get_collection("BotData")
    print("✅ Successfully connected to the cloud database!")
except Exception as e:
    print(f"❌ FATAL: Could not connect to MongoDB: {e}")
    exit(1)

def load_db_data():
    """Loads data from MongoDB."""
    data_doc = collection.find_one({"_id": "main_bot_config"})
    return data_doc if data_doc else {}

def save_db_data(data):
    """Saves data to MongoDB."""
    try:
        collection.update_one({"_id": "main_bot_config"}, {"$set": data}, upsert=True)
    except Exception as e:
        print(f"ERROR saving data to MongoDB: {e}")
