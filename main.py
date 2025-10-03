import os
import asyncio
from aiogram import executor
from flask import Flask, request
from threading import Thread

from loader import dp, bot
from handlers import admin, user
from utils import tasks
import data_store

# --- Web Server to Keep Bot Alive on Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot server is running!"

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# --- Bot Startup Logic ---
async def on_startup(dispatcher):
    """Function to run on bot startup."""
    print("Bot is starting up...")
    
    # Register all handlers
    admin.register_admin_handlers(dispatcher)
    user.register_user_handlers(dispatcher)
    
    # Start background tasks
    await tasks.startup_tasks(dispatcher)
    
    # Send startup message to admin
    try:
        await bot.send_message(data_store.config.ADMIN_CHAT_ID, "✅ **تم تشغيل البوت بنجاح!**\n\n- البوت متصل وجاهز لاستقبال الرسائل.\n- خادم الويب يعمل.\n- المهام الخلفية نشطة.")
    except Exception as e:
        print(f"Warning: Could not send startup message to admin. {e}")
        
    print("✅ Bot is online and ready!")

# --- Main Entry Point ---
if __name__ == '__main__':
    # Start the web server in a separate thread
    web_thread = Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    # Start the bot polling
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
