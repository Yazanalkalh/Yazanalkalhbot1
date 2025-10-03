import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env (للتشغيل المحلي)
load_dotenv()

# --- المتغيرات الأساسية ---
# توكن البوت الذي تحصل عليه من BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN")

# معرف حسابك الرقمي في تيليجرام لتلقي الرسائل واستخدام لوحة التحكم
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# رابط الاتصال بقاعدة بيانات MongoDB Atlas
MONGO_URI = os.getenv("MONGO_URI")

# --- التحقق من وجود المتغيرات ---
print("🔍 Checking environment variables...")
if not all([BOT_TOKEN, ADMIN_CHAT_ID, MONGO_URI]):
    print("❌ Critical Error: BOT_TOKEN, ADMIN_CHAT_ID, and MONGO_URI must be set in environment variables!")
    exit(1)

try:
    ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)
    print(f"✅ Admin ID has been set: {ADMIN_CHAT_ID}")
except ValueError:
    print("❌ Critical Error: ADMIN_CHAT_ID must be a valid integer.")
    exit(1)
