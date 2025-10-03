import os
import sys
import asyncio
from aiogram.utils import executor
import atexit

# --- THIS IS THE RADICAL FIX: A LOCK FILE TO PREVENT DUPLICATE INSTANCES ---
LOCK_FILE = "bot.lock"

def create_lock_file():
    if os.path.exists(LOCK_FILE):
        print("❌ FATAL: Another instance is already running. Lock file exists.")
        sys.exit(1)
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    print("✅ Lock file created. This is the only running instance.")

def remove_lock_file():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
        print("✅ Lock file removed on exit.")

# Create lock on startup and register removal on exit
create_lock_file()
atexit.register(remove_lock_file)
# --------------------------------------------------------------------------

from loader import dp
from handlers import register_all_handlers
from utils.background_tasks import startup_tasks
from web_server import run_web_server
from threading import Thread

async def on_startup(dispatcher):
    """Function to run on bot startup."""
    register_all_handlers(dispatcher)
    await startup_tasks(dispatcher)

if __name__ == '__main__':
    try:
        # Start the web server in a separate thread
        web_thread = Thread(target=run_web_server)
        web_thread.daemon = True
        web_thread.start()

        # Start the bot
        print("Starting bot polling...")
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")
    finally:
        remove_lock_file()
