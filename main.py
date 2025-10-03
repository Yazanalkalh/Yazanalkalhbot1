import os
import asyncio
from aiogram.utils import executor
from threading import Thread

# This lock file logic is good practice for polling bots on servers
# to prevent accidental multiple instances.
LOCK_FILE = "bot.lock"
if os.path.exists(LOCK_FILE):
    print("⚠️ WARNING: Lock file exists. Another instance might be running.")
    # You might want to handle this more gracefully in production
    # For now, we remove it to allow starting.
    os.remove(LOCK_FILE)

with open(LOCK_FILE, "w") as f:
    f.write("locked")

from loader import dp
from handlers import register_all_handlers
import data_store
from utils.background_tasks import startup_tasks
from web_server import run_web_server # We still need this to keep Render alive

async def on_startup(dispatcher):
    """Function to run on bot startup."""
    # Initialize bot data from the database
    data_store.initialize_data()
    # Register all handlers
    register_all_handlers(dispatcher)
    # Run background tasks
    await startup_tasks(dispatcher)

def on_shutdown(dispatcher):
    """Function to run on bot shutdown."""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
    print("Bot shutdown complete. Lock file removed.")

if __name__ == '__main__':
    # Start the web server in a separate thread to keep the service alive
    web_thread = Thread(target=run_web_server, daemon=True)
    web_thread.start()

    # Start the bot using polling
    print("Starting bot polling...")
    executor.start_polling(
        dp, 
        skip_updates=True, 
        on_startup=on_startup, 
        on_shutdown=on_shutdown
    )
