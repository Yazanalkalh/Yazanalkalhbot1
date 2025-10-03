import os
import sys
import asyncio
from aiogram.utils import executor
import atexit
from threading import Thread

# --- THIS IS THE RADICAL FIX: REMOVED THE COMPLEX LOCK ---
# We use a simple method without a file to avoid the I/O error
# The original lock logic was the source of this NoneType error.

from loader import dp
from handlers import register_all_handlers
from utils.background_tasks import startup_tasks
from web_server import run_web_server
import data_store

async def on_startup(dispatcher):
    """Function to run on bot startup."""
    # Initialize bot data from database
    data_store.initialize_data()
    # Register all handlers
    register_all_handlers(dispatcher)
    # Run background tasks
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
        print("Bot stopped gracefully.")
