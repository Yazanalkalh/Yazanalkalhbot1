import os
import sys
import atexit

# --- Lock File to prevent duplicate instances ---
LOCK_FILE = "bot.lock"
def create_lock_file():
    if os.path.exists(LOCK_FILE):
        print("❌ FATAL: Lock file exists. Another instance may be running.")
        sys.exit(1)
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    print("✅ Lock file created.")

def remove_lock_file():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
        print("✅ Lock file removed.")

create_lock_file()
atexit.register(remove_lock_file)
# -------------------------------------------------

from aiogram.utils import executor
from threading import Thread

from loader import dp
from handlers import register_all_handlers
from utils.background_tasks import startup_tasks
from web_server import run_web_server
import data_store # Import the data_store module

async def on_startup(dispatcher):
    """Function to run on bot startup."""
    # --- THIS IS THE CRITICAL FIX ---
    # Initialize the bot's data and settings from the database and defaults.
    data_store.initialize_data()
    # ---------------------------------
    
    register_all_handlers(dispatcher)
    await startup_tasks(dispatcher)

if __name__ == '__main__':
    try:
        web_thread = Thread(target=run_web_server, daemon=True)
        web_thread.start()
        print("Starting bot polling...")
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped by user.")
    finally:
        remove_lock_file() 
