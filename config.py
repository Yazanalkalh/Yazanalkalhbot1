import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env (للتشغيل المحلي)
load_dotenv()

# قراءة المتغيرات من بيئة التشغيل (Render) أو ملف .env
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID_STR = os.getenv("ADMIN_CHAT_ID")
MONGO_URI = os.getenv("MONGO_URI")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# التحقق من وجود المتغيرات الأساسية
if not all([API_TOKEN, ADMIN_CHAT_ID_STR, MONGO_URI]):
    print("❌ خطأ فادح: تأكد من وجود BOT_TOKEN, ADMIN_CHAT_ID, MONGO_URI في متغيرات البيئة!")
    exit(1)

# تحويل آيدي المشرف إلى رقم صحيح مع معالجة الأخطاء
try:
    ADMIN_CHAT_ID = int(ADMIN_CHAT_ID_STR)
    print(f"✅ تم تعيين المشرف: {ADMIN_CHAT_ID}")
except (ValueError, TypeError):
    print(f"❌ خطأ فادح: قيمة ADMIN_CHAT_ID ({ADMIN_CHAT_ID_STR}) ليست رقماً صحيحاً!")
    exit(1)

print("✅ جميع متغيرات البيئة الأساسية موجودة.")
