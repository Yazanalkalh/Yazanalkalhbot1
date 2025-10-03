import os
from threading import Thread
from flask import Flask
from aiogram import executor
from loader import dp
from handlers import admin, user
from utils.tasks import startup_tasks

# --- Web Server to keep the bot alive ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot server is running!"

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# --- Bot Startup Function ---
async def on_startup(dispatcher):
    """
    Executes when the bot starts up.
    """
    # Register message handlers
    user.register_user_handlers(dispatcher)
    admin.register_admin_handlers(dispatcher)
    
    # Start background tasks
    await startup_tasks(dispatcher)
    
    print("🚀 Bot has been started and is running!")

# --- Main entry point ---
if __name__ == '__main__':
    # Start the web server in a separate thread
    web_thread = Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    # Start the bot
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
