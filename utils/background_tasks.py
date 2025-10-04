import asyncio
import datetime
import random
from loader import bot
from config import ADMIN_CHAT_ID
import data_store
# NEW: We import the specific, upgraded database functions
from utils.database import get_due_scheduled_posts, get_content_from_library, mark_post_as_sent

# This function is UNCHANGED as it handles random recurring posts, not the new library.
async def schedule_channel_messages():
    """Periodically sends a random message from the old channel_messages list."""
    while True:
        try:
            settings = data_store.bot_data.get('bot_settings', {})
            interval = settings.get('schedule_interval_seconds', 86400)
            await asyncio.sleep(interval)

            channel_id = settings.get('channel_id')
            messages = data_store.bot_data.get('channel_messages', [])

            if channel_id and messages:
                message_text = random.choice(messages)
                await bot.send_message(channel_id, message_text)
                print(f"✅ Auto-posted random message to channel {channel_id}")
        except Exception as e:
            print(f"CHANNEL SCHEDULER ERROR: {e}")
            await asyncio.sleep(60)

# --- UPGRADED: This is the new "Shipping Coordinator" ---
async def process_scheduled_posts():
    """
    UPGRADED: This function now works with the Content Library.
    It fetches due posts, gets the original content from the library,
    and sends it using the correct method (text, sticker, photo).
    """
    while True:
        try:
            await asyncio.sleep(30) # Check for due posts every 30 seconds
            
            # 1. Ask the "Warehouse Manager" for due shipments
            due_posts = get_due_scheduled_posts()

            if not due_posts:
                continue # No work to do, wait for the next cycle

            print(f"Processing {len(due_posts)} scheduled post(s)...")

            for post in due_posts:
                try:
                    # 2. Get the original product from the library using its reference ID
                    content_doc = get_content_from_library(post['content_id'])

                    if not content_doc:
                        print(f"⚠️ Could not find content with ID {post['content_id']}. Skipping.")
                        mark_post_as_sent(post['_id']) # Mark as sent to avoid repeated errors
                        continue

                    content_type = content_doc['type']
                    content_value = content_doc['value']
                    channel_id = post['channel_id']

                    # 3. Choose the correct delivery truck based on the content type
                    if content_type == 'text':
                        await bot.send_message(channel_id, content_value)
                    elif content_type == 'sticker':
                        await bot.send_sticker(channel_id, content_value)
                    elif content_type == 'photo':
                        await bot.send_photo(channel_id, content_value)
                    
                    print(f"✅ Sent scheduled {content_type} to {channel_id}")

                    # 4. Confirm delivery to the "Warehouse Manager"
                    mark_post_as_sent(post['_id'])

                except Exception as e:
                    print(f"SCHEDULED POST SEND ERROR for post {post['_id']}: {e}")
                    # We don't mark it as sent, so the bot will retry on the next cycle

        except Exception as e:
            print(f"SCHEDULED POST PROCESSOR ERROR: {e}")
            await asyncio.sleep(60) # Wait a minute before retrying on major error


# This function is UNCHANGED. It correctly starts all background tasks.
async def startup_tasks(dp):
    """Tasks to run on bot startup."""
    try:
        await bot.send_message(
            ADMIN_CHAT_ID,
            (
                "✅ <b>البوت يعمل بنجاح! (إصدار مكتبة المحتوى)</b>\n\n"
                "- <b>الحالة:</b> متصل ونشط\n"
                "- <b>الخادم:</b> يعمل\n"
                "- <b>قاعدة البيانات:</b> متصلة\n\n"
                "<i>جاهز لاستقبال الرسائل.</i>"
            )
        )
        # Start both the old random scheduler and the new smart scheduler
        asyncio.create_task(schedule_channel_messages())
        asyncio.create_task(process_scheduled_posts())
        print("✅ Background tasks (including new scheduler) started.")
    except Exception as e:
        print(f"STARTUP NOTIFICATION ERROR: {e}")


