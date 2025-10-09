import asyncio
from loader import bot
from config import ADMIN_CHAT_ID
from utils import database

async def daily_reminder_task():
    """A background task that could send a daily reminder to a channel."""
    # This is a placeholder for a more complex scheduler you might want.
    # For now, it runs once on startup as an example.
    try:
        channel_id = database.get_setting("main_channel_id")
        if channel_id:
            reminder = database.get_random_reminder()
            await bot.send_message(channel_id, reminder)
            print(f"✅ Sent a startup reminder to channel {channel_id}")
    except Exception as e:
        print(f"DAILY REMINDER TASK ERROR: {e}")


async def startup_tasks(dp):
    """Tasks to run on bot startup."""
    try:
        await bot.send_message(
            ADMIN_CHAT_ID,
            "✅ **Bot is running (VIP Edition)!**\n\n- <b>Status:</b> Online and active\n- <b>Database:</b> SYNC Stable"
        )
        # Start any recurring background tasks here
        asyncio.create_task(daily_reminder_task())
        print("✅ Background tasks started.")
    except Exception as e:
        print(f"STARTUP NOTIFICATION ERROR: {e}")
