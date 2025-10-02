import asyncio
from threading import Thread
from flask import Flask
from aiogram import executor

# استيراد المكونات الأساسية للبوت
from loader import dp, bot
from utils.tasks import startup_tasks
from handlers import admin, user

# --- إعداد خادم الويب (للتشغيل على Render) ---
app = Flask(__name__)

@app.route('/')
def home():
    """صفحة بسيطة لتأكيد أن الخادم يعمل."""
    return "Bot server is running smoothly!"

def run_web_server():
    """تشغيل خادم الويب في الخلفية."""
    # Render يحدد المنفذ تلقائيًا، 10000 هو خيار احتياطي
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# --- دالة بدء التشغيل ---
async def on_startup(dispatcher):
    """
    يتم تنفيذ هذه الدالة عند بدء تشغيل البوت.
    تقوم بتسجيل المعالجات وبدء المهام الخلفية.
    """
    # تسجيل معالجات المشرف والمستخدم
    admin.register_admin_handlers(dispatcher)
    user.register_user_handlers(dispatcher)

    # --- **هذا هو السطر الذي تم تصحيحه** ---
    # الآن نقوم بتمرير 'dispatcher' (المعروف بـ dp) إلى دالة بدء المهام
    await startup_tasks(dispatcher)

# --- نقطة انطلاق البرنامج الرئيسية ---
if __name__ == "__main__":
    # بدء تشغيل خادم الويب في خيط منفصل ليبقى البوت نشطًا
    web_thread = Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    # بدء تشغيل البوت باستخدام Polling
    print("🤖 The bot is starting...")
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)


