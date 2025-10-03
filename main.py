import os
import asyncio
from flask import Flask
from threading import Thread
from aiogram.utils import executor

from loader import dp
from handlers import admin, user
import data_store
from utils.tasks import startup_tasks

# --- Web Server to Keep Bot Alive on Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# --- Bot Startup Logic ---
async def on_startup(dispatcher):
    """Function to run on bot startup."""
    # Initialize bot data from database
    data_store.initialize_data()
    
    # Register all handlers
    user.register_user_handlers(dispatcher)
    admin.register_admin_handlers(dispatcher)
    
    # Run background tasks
    await startup_tasks(dispatcher)

if __name__ == '__main__':
    # Start the web server in a separate thread
    web_thread = Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()

    # Start the bot
    print("Starting bot polling...")
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
