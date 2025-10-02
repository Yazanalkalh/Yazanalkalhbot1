import asyncio
from threading import Thread
from flask import Flask
from aiogram import executor

from loader import dp, bot
from handlers.user import register_user_handlers
from handlers.admin import register_admin_handlers
from utils.tasks import startup_tasks
from config import ADMIN_CHAT_ID

# --- خادم الويب لإبقاء البوت نشطًا ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot server is running!"

def run_web_server(port):
    app.run(host='0.0.0.0', port=port)

# --- دالة بدء التشغيل ---
async def on_startup(dispatcher):
    """
    تنفذ عند بدء تشغيل البوت.
    """
    # تسجيل جميع معالجات الرسائل والأوامر
    register_admin_handlers(dispatcher)
    register_user_handlers(dispatcher)

    # بدء المهام الخلفية
    asyncio.create_task(startup_tasks())

    # إرسال رسالة تأكيد للمشرف
    try:
        await bot.send_message(ADMIN_CHAT_ID, "✅ **البوت يعمل الآن بنجاح!**\n\n"
                                             "جميع الوحدات تم تحميلها والمهام الخلفية بدأت.",
                                             parse_mode="Markdown")
    except Exception as e:
        print(f"تحذير: لم يتم إرسال رسالة البدء للمشرف: {e}")
    
    print("🤖 Bot is up and running!")

# --- نقطة انطلاق البرنامج ---
if __name__ == '__main__':
    import os
    # بدء خادم الويب في خيط منفصل
    port = int(os.environ.get('PORT', 10000))
    web_thread = Thread(target=run_web_server, args=(port,))
    web_thread.daemon = True
    web_thread.start()
    
    # بدء البوت
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)


 
