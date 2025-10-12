import asyncio
import datetime
import random
import pytz
from loader import bot
from config import ADMIN_CHAT_ID
import data_store

async def schedule_channel_messages():
    """Periodically sends a random message to the configured channel."""
    while True:
        try:
            settings = data_store.bot_data['bot_settings']
            interval = settings.get('schedule_interval_seconds', 86400)
            await asyncio.sleep(interval)

            channel_id = settings.get('channel_id')
            messages = data_store.bot_data.get('channel_messages', [])

            if channel_id and messages:
                message_text = random.choice(messages)
                await bot.send_message(channel_id, message_text)
                print(f"✅ Auto-posted to channel {channel_id}")
        except Exception as e:
            print(f"CHANNEL SCHEDULER ERROR: {e}")
            await asyncio.sleep(60) # Wait a minute before retrying on error

async def process_scheduled_posts():
    """Processes one-time scheduled posts."""
    while True:
        try:
            await asyncio.sleep(30) # Check every 30 seconds
            now_utc = pytz.utc.localize(datetime.datetime.utcnow())
            
            posts_to_send = []
            remaining_posts = []

            for post in data_store.bot_data.get("scheduled_posts", []):
                send_at = datetime.datetime.fromisoformat(post['send_at_iso'])
                if send_at <= now_utc:
                    posts_to_send.append(post)
                else:
                    remaining_posts.append(post)

            if posts_to_send:
                for post in posts_to_send:
                    try:
                        await bot.send_message(post['channel_id'], post['text'])
                        print(f"✅ Sent scheduled post to {post['channel_id']}")
                    except Exception as e:
                        print(f"SCHEDULED POST ERROR: {e}")
                
                data_store.bot_data["scheduled_posts"] = remaining_posts
                data_store.save_data()

        except Exception as e:
            print(f"SCHEDULED POST PROCESSOR ERROR: {e}")

async def startup_tasks(dp):
    """Tasks to run on bot startup."""
    try:
        await bot.send_message(
            ADMIN_CHAT_ID,
            (
                "✅ <b>البوت يعمل بنجاح!</b>\n\n"
                "- <b>الحالة:</b> متصل ونشط\n"
                "- <b>الخادم:</b> يعمل\n"
                "- <b>قاعدة البيانات:</b> متصلة\n\n"
                "<i>جاهز لاستقبال الرسائل.</i>"
            )
        )
        asyncio.create_task(schedule_channel_messages())
        asyncio.create_task(process_scheduled_posts())
        print("✅ Background tasks started.")
    except Exception as e:
        print(f"STARTUP NOTIFICATION ERROR: {e}")
