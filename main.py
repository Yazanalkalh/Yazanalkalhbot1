import os
import sys
import atexit
from threading import Thread

# --- Lock File logic to prevent duplicate instances (Unchanged) ---
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
# --------------------------------------------------------------------

from aiogram.utils import executor
from loader import dp
from handlers import register_all_handlers
# --- NEW: 1. Import the registration function for our "new lamp" ---
from handlers.admins.text_manager_handler import register_text_manager_handler
from utils.background_tasks import startup_tasks
from web_server import run_web_server
import data_store

async def on_startup(dispatcher):
    """Function to run on bot startup."""
    data_store.initialize_data()
    
    # Register all the old, working handlers
    register_all_handlers(dispatcher)
    
    # --- NEW: 2. Plug in the "new lamp" ---
    register_text_manager_handler(dispatcher)
    
    await startup_tasks(dispatcher)

if __name__ == '__main__':
    try:
        web_thread = Thread(target=run_web_server, daemon=True)
        web_thread.start()
        print("Starting bot polling...")
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")
    finally:
        remove_lock_file()
