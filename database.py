from pymongo import MongoClient
from config import MONGO_URI
import data_store

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("HijriBotDB")
    collection = db.get_collection("BotDataV3") # Using a new version for clean start
    print("✅ Successfully connected to the cloud database!")
except Exception as e:
    print(f"❌ Database Connection Failed: {e}")
    exit(1)

def load_all_data():
    """Loads all data, merging with defaults to prevent errors."""
    data_doc = collection.find_one({"_id": "main_bot_config"})
    
    # Deep copy the default settings to avoid modifying the original
    import copy
    final_data = copy.deepcopy(data_store.DEFAULT_SETTINGS)

    if data_doc:
        # Recursively update the default dictionary with data from the database
        def recursive_update(default, db_data):
            for key, value in db_data.items():
                if isinstance(value, dict) and isinstance(default.get(key), dict):
                    recursive_update(default[key], value)
                else:
                    default[key] = value
        recursive_update(final_data, data_doc)
        
    return final_data

def save_all_data(data):
    """Saves the complete data structure to the database."""
    try:
        data_to_save = data.copy()
        data_to_save.pop("_id", None)
        collection.update_one(
            {"_id": "main_bot_config"},
            {"$set": data_to_save},
            upsert=True
        )
    except Exception as e:
        print(f"Error saving data to MongoDB: {e}")
