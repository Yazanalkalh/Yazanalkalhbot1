import os
import sys
import atexit
import time
from threading import Thread

# --- THIS IS THE RADICAL FIX: A ROBUST LOCK FILE TO PREVENT DUPLICATE INSTANCES ---
LOCK_FILE = "bot.lock"

def create_lock_file():
    """Create a lock file to ensure only one instance runs."""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                pid = int(f.read().strip())
            # Check if the process with that PID is still running (works on Linux)
            if os.path.exists(f"/proc/{pid}"):
                print(f"❌ FATAL: Another instance (PID: {pid}) is already running. Lock file exists.")
                sys.exit(1) # Exit immediately if another instance is running
            else:
                # The lock file is stale (from a previous crashed run)
                print("⚠️ WARNING: Stale lock file found. Removing it.")
                os.remove(LOCK_FILE)
        except (IOError, ValueError):
            print("⚠️ WARNING: Could not read stale lock file. Removing it.")
            os.remove(LOCK_FILE)

    # Create a new lock file with the current process ID
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    print(f"✅ Lock file created for PID: {os.getpid()}. This is the only running instance.")

def remove_lock_file():
    """Remove the lock file on exit."""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
        print("✅ Lock file removed on clean exit.")

# Register the cleanup function to be called on normal exit
atexit.register(remove_lock_file)
# Create the lock at the very beginning
create_lock_file()
# --------------------------------------------------------------------------

# We import the bot components AFTER the lock is secured
from aiogram.utils import executor
from loader import dp
from handlers import register_all_handlers
from utils.background_tasks import startup_tasks
from web_server import run_web_server
import data_store

async def on_startup(dispatcher):
    """Function to run on bot startup."""
    data_store.initialize_data()
    register_all_handlers(dispatcher)
    await startup_tasks(dispatcher)

if __name__ == '__main__':
    try:
        # Start the web server in a separate thread
        web_thread = Thread(target=run_web_server, daemon=True)
        web_thread.start()

        # Start the bot
        print("Starting bot polling...")
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped by user or system exit.")
    
    finally:
        # This ensures the lock file is removed even if the bot crashes
        remove_lock_file()
