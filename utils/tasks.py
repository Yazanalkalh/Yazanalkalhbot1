import asyncio
import datetime
import random
import pytz
from aiogram import Dispatcher
from loader import bot
import data_store

async def schedule_channel_messages():
    """Periodically sends a random message to the configured channel."""
    while True:
        try:
            cfg = data_store.bot_data['bot_settings']
            interval = cfg.get('schedule_interval_seconds', 86400)
            await asyncio.sleep(interval)
            
            channel_id = cfg.get('channel_id')
            messages = data_store.bot_data.get('channel_messages', [])
            
            if channel_id and messages:
                message_text = random.choice(messages)
                await bot.send_message(chat_id=channel_id, text=message_text)
        except Exception as e:
            print(f"Error in scheduled message task: {e}")
            await asyncio.sleep(60) # Wait a minute before retrying on error

async def check_scheduled_posts():
    """Checks for and sends specifically scheduled posts."""
    while True:
        try:
            await asyncio.sleep(60) # Check every minute
            now_utc = pytz.utc.localize(datetime.datetime.utcnow())
            
            posts_to_send = []
            remaining_posts = []
            
            for post in data_store.bot_data.get("scheduled_posts", []):
                send_at = datetime.datetime.fromisoformat(post['send_at_iso'])
                if now_utc >= send_at:
                    posts_to_send.append(post)
                else:
                    remaining_posts.append(post)

            if posts_to_send:
                for post in posts_to_send:
                    try:
                        await bot.send_message(chat_id=post['channel_id'], text=post['text'])
                    except Exception as e:
                        print(f"Failed to send scheduled post: {e}")
                
                data_store.bot_data['scheduled_posts'] = remaining_posts
                data_store.save_data()

        except Exception as e:
            print(f"Error in scheduled post checker: {e}")

async def startup_tasks(dp: Dispatcher):
    """Tasks to run on bot startup."""
    asyncio.create_task(schedule_channel_messages())
    asyncio.create_task(check_scheduled_posts())
    print("✅ Background tasks started.") 
