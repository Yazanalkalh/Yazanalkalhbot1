from pymongo import MongoClient
from config import MONGO_URI
import data_store # استدعاء مخزن البيانات للحصول على القالب الافتراضي

# --- إعداد الاتصال بقاعدة البيانات ---
try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("HijriBotDB")
    collection = db.get_collection("BotDataV2") # تم تغيير اسم الجدول لضمان بداية نظيفة
    print("✅ Successfully connected to the cloud database!")
except Exception as e:
    print(f"❌ Database Connection Failed: {e}")
    exit(1)

def load_all_data():
    """
    تحميل جميع بيانات البوت من قاعدة البيانات.
    إذا لم يتم العثور على بيانات، يتم استخدام القالب الافتراضي من data_store.
    """
    data_doc = collection.find_one({"_id": "main_bot_config"})
    if data_doc:
        # دمج البيانات المحملة مع القالب الافتراضي لضمان وجود كل المفاتيح
        # هذا يمنع الأخطاء عند إضافة إعدادات جديدة في المستقبل
        default_copy = data_store.DEFAULT_SETTINGS.copy()
        default_copy.update(data_doc)
        return default_copy
    else:
        # إذا لم يكن هناك أي مستند في قاعدة البيانات، استخدم القالب الافتراضي
        print("⚠️ No data found in DB, using default settings.")
        return data_store.DEFAULT_SETTINGS.copy()

def save_all_data(data):
    """
    حفظ القاموس الكامل لبيانات البوت في قاعدة البيانات.
    يستخدم أمر upsert=True لإنشاء المستند إذا لم يكن موجوداً.
    """
    try:
        # إزالة حقل _id إذا كان موجوداً لتجنب الأخطاء
        data.pop("_id", None)
        collection.update_one(
            {"_id": "main_bot_config"},
            {"$set": data},
            upsert=True
        )
    except Exception as e:
        print(f"Error saving data to MongoDB: {e}")
