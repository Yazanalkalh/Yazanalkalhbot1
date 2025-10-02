import os
from threading import Thread
from flask import Flask
from aiogram import executor

from loader import dp
from handlers import admin, user
from utils.tasks import startup_tasks
from config import ADMIN_CHAT_ID

# --- إعداد خادم الويب (للتشغيل على Render) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot server is running smoothly!"

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# --- دالة بدء تشغيل البوت ---
async def on_startup(dispatcher):
    # تسجيل معالجات المستخدم والمشرف
    user.register_user_handlers(dispatcher)
    admin.register_admin_handlers(dispatcher)

    # إرسال رسالة بدء التشغيل وجدولة المهام
    await startup_tasks(dispatcher)

# --- نقطة انطلاق البرنامج ---
if __name__ == '__main__':
    # بدء تشغيل خادم الويب في خيط منفصل
    web_thread = Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    # بدء تشغيل البوت
    print("🤖 Bot is starting polling...")
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
