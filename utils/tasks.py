import asyncio
import datetime
import random
from loader import bot
from config import CHANNEL_ID, ADMIN_CHAT_ID
from .helpers import bot_data, CHANNEL_MESSAGES, start_time, USERS_LIST, user_messages

async def send_channel_message(custom_message=None, channel_id_override=None):
    """Sends a message to the configured channel."""
    channel_id = channel_id_override or bot_data.get("channel_id") or CHANNEL_ID
    if not channel_id:
        print("❌ Channel ID is not specified.")
        return False
    if not CHANNEL_MESSAGES and not custom_message:
        print("❌ No messages are available to send.")
        return False
    try:
        message_to_send = custom_message or random.choice(CHANNEL_MESSAGES)
        if not channel_id.startswith('@') and not channel_id.startswith('-'):
            channel_id = '@' + channel_id
        await bot.send_message(chat_id=channel_id, text=message_to_send)
        print(f"✅ Message sent to channel: {channel_id}")
        return True
    except Exception as e:
        print(f"❌ Error sending message to channel: {e}")
        return False

async def schedule_channel_messages():
    """Periodically sends messages to the channel based on the schedule."""
    print("🕐 Starting scheduled messages for the channel...")
    while True:
        try:
            interval_seconds = bot_data.get("schedule_interval_seconds", 86400)
            await asyncio.sleep(interval_seconds)
            if bot_data.get("channel_id") or CHANNEL_ID:
                if CHANNEL_MESSAGES:
                    await send_channel_message()
        except Exception as e:
            print(f"❌ Error in message scheduler: {e}")
            await asyncio.sleep(60)

async def keep_alive_task():
    """Pings the bot API periodically to ensure the connection is alive."""
    ping_count = 0
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        ping_count += 1
        try:
            me = await bot.get_me()
            if ping_count % 6 == 0:  # Every 30 minutes, print a confirmation
                print(f"🔄 Keep-alive #{ping_count} - Bot is active: @{me.username}")
        except Exception as e:
            print(f"⚠️ Warning: Bot connection issue: {e}")

async def deployment_monitor():
    """Monitors the deployment and sends a daily report."""
    while True:
        await asyncio.sleep(3600)  # Every hour
        current_time = datetime.datetime.now()
        uptime_hours = (current_time - start_time).total_seconds() / 3600
        # Send a daily report around noon
        if current_time.hour == 12 and current_time.minute < 5:
            try:
                report = (
                    f"📊 **تقرير يومي - البوت يعمل بنجاح**\n\n"
                    f"⏰ وقت التشغيل: {uptime_hours:.1f} ساعة\n"
                    f"👥 المستخدمين: {len(USERS_LIST)}\n"
                    f"💬 الرسائل المحفوظة: {len(user_messages)}\n"
                    f"🌐 الخادم: نشط ومستقر"
                )
                await bot.send_message(ADMIN_CHAT_ID, report, parse_mode="Markdown")
            except Exception as e:
                print(f"Error sending daily report: {e}")
