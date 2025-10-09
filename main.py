import os
import sys
import atexit
from threading import Thread

# --- Lock File logic (لا تغيير هنا) ---
LOCK_FILE = "bot.lock"
def create_lock_file():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f: pid = int(f.read().strip())
            if os.path.exists(f"/proc/{pid}"):
                print(f"❌ FATAL: Another instance (PID: {pid}) is already running.")
                sys.exit(1)
            else: os.remove(LOCK_FILE)
        except (IOError, ValueError): os.remove(LOCK_FILE)
    with open(LOCK_FILE, "w") as f: f.write(str(os.getpid()))
    print(f"✅ Lock file created for PID: {os.getpid()}.")
def remove_lock_file():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
        print("✅ Lock file removed on clean exit.")
atexit.register(remove_lock_file)
create_lock_file()
# -----------------------------------

from aiogram.utils import executor
from aiogram import types # استيراد types
from loader import dp
from handlers import register_all_handlers
from utils.background_tasks import startup_tasks
from web_server import run_web_server
from config import ADMIN_CHAT_ID # استيراد ID المدير

async def on_startup(dispatcher):
    """(لا تغيير هنا)"""
    register_all_handlers(dispatcher)
    await startup_tasks(dispatcher)

# --- 🕵️‍♂️ الكود التشخيصي ---
# هذا المعالج المؤقت سيستجيب لأي رسالة من أي شخص
# ويقوم بطباعة المعلومات التي نحتاجها في سجلات Render
@dp.message_handler()
async def diagnostic_handler(message: types.Message):
    user_id = message.from_user.id
    admin_id = ADMIN_CHAT_ID
    
    print("--- 🕵️‍♂️ DIAGNOSTIC CHECK 🕵️‍♂️ ---")
    print(f"ID المستخدم الذي أرسل الرسالة: {user_id}")
    print(f"ID المدير المسجل في الإعدادات: {admin_id}")
    print(f"هل الأرقام متطابقة؟ -> {user_id == admin_id}")
    print("---------------------------------")
# -----------------------------

if __name__ == '__main__':
    try:
        web_thread = Thread(target=run_web_server, daemon=True)
        web_thread.start()
        print("Starting bot polling for diagnostics...")
        # لاحظ أننا لم نعد نسجل المعالجات في on_startup لتجنب التضارب مع التشخيص
        executor.start_polling(dp, skip_updates=True) 
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")
    finally:
        remove_lock_file()
