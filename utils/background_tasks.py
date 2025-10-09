import asyncio
import datetime
import random
from loader import bot
from config import ADMIN_CHAT_ID
import data_store
# We import the specific, upgraded database functions
from utils.database import get_due_scheduled_posts, get_content_from_library, mark_post_as_sent

# This function remains unchanged.
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

# --- UPGRADED: The "Shipping Coordinator" now has a walkie-talkie ---
async def process_scheduled_posts():
    """
    UPGRADED: This function now sends success/fail notifications to the admin
    based on the settings in the advanced panel.
    """
    while True:
        try:
            await asyncio.sleep(30)
            
            due_posts = get_due_scheduled_posts()
            if not due_posts:
                continue

            notification_settings = data_store.bot_data.get('notification_settings', {})

            for post in due_posts:
                content_doc = get_content_from_library(post['content_id'])
                channel_id_to_post = post.get('channel_id', 'N/A')

                try:
                    if not content_doc:
                        raise ValueError(f"المحتوى ID {post['content_id']} لم يعد موجودًا في المكتبة.")

                    content_type = content_doc['type']
                    content_value = content_doc['value']

                    if content_type == 'text':
                        await bot.send_message(channel_id_to_post, content_value)
                    elif content_type == 'sticker':
                        await bot.send_sticker(channel_id_to_post, content_value)
                    elif content_type == 'photo':
                        await bot.send_photo(channel_id_to_post, content_value)
                    
                    mark_post_as_sent(post['_id'])
                    print(f"✅ Sent scheduled {content_type} to {channel_id_to_post}")

                    # --- NEW: Success Notification Logic ---
                    if notification_settings.get('on_success', False):
                        await bot.send_message(ADMIN_CHAT_ID, f"✅ **إشعار نجاح**\n\nتم نشر المحتوى المجدول بنجاح في القناة `{channel_id_to_post}`.")

                except Exception as e:
                    print(f"SCHEDULED POST SEND ERROR for post {post['_id']}: {e}")
                    
                    # --- NEW: Failure Notification Logic ---
                    if notification_settings.get('on_fail', False):
                        error_message = str(e)
                        await bot.send_message(
                            ADMIN_CHAT_ID,
                            f"⚠️ **إشعار فشل**\n\nفشلت في نشر المحتوى المجدول في القناة `{channel_id_to_post}`.\n\n"
                            f"**سبب الخطأ:**\n`{error_message}`\n\n"
                            "سيحاول البوت إعادة الإرسال في الدورة التالية."
                        )

        except Exception as e:
            print(f"MAJOR SCHEDULED POST PROCESSOR ERROR: {e}")
            await asyncio.sleep(60)


# This function is unchanged.
async def startup_tasks(dp):
    """Tasks to run on bot startup."""
    try:
        await bot.send_message(
            ADMIN_CHAT_ID,
            "✅ **البوت يعمل بنجاح!**\n\n- <b>الحالة:</b> متصل ونشط\n- <b>الخادم:</b> يعمل"
        )
        asyncio.create_task(schedule_channel_messages())
        asyncio.create_task(process_scheduled_posts())
        print("✅ Background tasks started.")
    except Exception as e:
        print(f"STARTUP NOTIFICATION ERROR: {e}")
