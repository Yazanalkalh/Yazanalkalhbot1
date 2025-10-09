import asyncio
import random
from loader import bot
from config import ADMIN_CHAT_ID
from utils import database

async def schedule_channel_messages():
    while True:
        try:
            interval = await database.get_setting("schedule_interval_seconds", 86400)
            await asyncio.sleep(interval)
            channel_id = await database.get_setting("channel_id")
            messages = await database.get_all_channel_messages()
            if channel_id and messages:
                message_text = random.choice(messages)
                await bot.send_message(channel_id, message_text)
                print(f"✅ Auto-posted random message to channel {channel_id}")
        except Exception as e:
            print(f"CHANNEL SCHEDULER ERROR: {e}")
            await asyncio.sleep(60)

async def process_scheduled_posts():
    while True:
        try:
            await asyncio.sleep(30)
            due_posts = await database.get_due_scheduled_posts()
            if not due_posts:
                continue
            notify_on_success = await database.get_setting("notification_on_success", False)
            notify_on_fail = await database.get_setting("notification_on_fail", False)
            for post in due_posts:
                content_doc = await database.get_content_from_library(post['content_id'])
                channel_id_to_post = post.get('channel_id', 'N/A')
                try:
                    if not content_doc:
                        raise ValueError(f"Content ID {post['content_id']} not found.")
                    await bot.send_message(channel_id_to_post, content_doc['value'])
                    await database.mark_post_as_sent(post['_id'])
                    print(f"✅ Sent scheduled content to {channel_id_to_post}")
                    if notify_on_success:
                        await bot.send_message(ADMIN_CHAT_ID, f"✅ Success: Post sent to `{channel_id_to_post}`.")
                except Exception as e:
                    print(f"SCHEDULED POST SEND ERROR: {e}")
                    if notify_on_fail:
                        await bot.send_message(ADMIN_CHAT_ID, f"⚠️ Failure: Could not send to `{channel_id_to_post}`.\nReason: `{e}`")
        except Exception as e:
            print(f"MAJOR SCHEDULED POST PROCESSOR ERROR: {e}")
            await asyncio.sleep(60)

async def startup_tasks(dp):
    try:
        await bot.send_message(ADMIN_CHAT_ID, "✅ **Bot is running!**")
        asyncio.create_task(schedule_channel_messages())
        asyncio.create_task(process_scheduled_posts())
        print("✅ Background tasks started.")
    except Exception as e:
        print(f"STARTUP NOTIFICATION ERROR: {e}")
