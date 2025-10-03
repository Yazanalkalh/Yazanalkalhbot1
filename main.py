import os
import asyncio
from threading import Thread
from flask import Flask
from aiogram import executor
from loader import dp
from handlers import admin, user
from utils.tasks import startup_tasks

# --- خادم الويب لإبقاء البوت نشطاً ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot server is running!"

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# --- دالة بدء التشغيل ---
async def on_startup(dispatcher):
    """
    يتم تنفيذها عند بدء تشغيل البوت.
    """
    # تسجيل معالجات الرسائل
    user.register_user_handlers(dispatcher)
    admin.register_admin_handlers(dispatcher)
    
    # بدء المهام الخلفية
    await startup_tasks(dispatcher)
    
    print("🚀 Bot has been started and is running!")

# --- نقطة انطلاق البرنامج ---
if __name__ == '__main__':
    # بدء خادم الويب في خيط منفصل
    web_thread = Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    # بدء البوت
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
