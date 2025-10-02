import asyncio
import os
from threading import Thread
from flask import Flask
from aiogram import executor

# Import core bot components, handlers, and tasks
from loader import dp, bot
from config import ADMIN_CHAT_ID
from handlers import admin, user
from utils.tasks import schedule_channel_messages, keep_alive_task, deployment_monitor

# --- Web server to keep the bot alive on Render ---
app = Flask(__name__)
@app.route('/')
def home():
    """A simple route to confirm the web server is operational."""
    return "Bot server is running!"

def run_web_server():
    """Runs the Flask web server in a separate thread."""
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# --- Bot Startup Function ---
async def on_startup(dispatcher):
    """Function executed when the bot starts up."""
    # Register all handlers from the handlers package
    admin.register_admin_handlers(dispatcher)
    user.register_user_handlers(dispatcher)

    # Start background tasks
    asyncio.create_task(schedule_channel_messages())
    asyncio.create_task(keep_alive_task())
    asyncio.create_task(deployment_monitor())

    print("✅ Bot is ready to work 24/7!")
    
    # Send a confirmation message to the admin
    try:
        await bot.send_message(
            ADMIN_CHAT_ID,
            "✅ **البوت يعمل بنجاح!**\n\n"
            "🤖 البوت متصل ونشط\n"
            "🌐 خادم الويب يعمل\n"
            "☁️ قاعدة البيانات متصلة",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Warning: Could not send startup message to admin: {e}")

# --- Main entry point of the application ---
if __name__ == "__main__":
    # Start the web server in a non-blocking thread
    web_server_thread = Thread(target=run_web_server)
    web_server_thread.daemon = True
    web_server_thread.start()
    
    # Start the bot polling
    print("🤖 Starting the bot...")
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)


