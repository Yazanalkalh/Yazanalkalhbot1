import asyncio
import random
from loader import bot
from config import ADMIN_CHAT_ID
from utils import database

# هذه الدالة يجب أن تبقى async لأنها تستخدم asyncio.sleep
async def schedule_channel_messages():
    while True:
        try:
            # ✅ تم الإصلاح: لا يوجد await لاستدعاءات قاعدة البيانات
            interval = database.get_setting("schedule_interval_seconds", 86400)
            await asyncio.sleep(interval)
            channel_id = database.get_setting("channel_id")
            messages = database.get_all_channel_messages()
            if channel_id and messages:
                message_text = random.choice(messages)
                await bot.send_message(channel_id, message_text)
                print(f"✅ Auto-posted random message to channel {channel_id}")
        except Exception as e:
            print(f"CHANNEL SCHEDULER ERROR: {e}")
            await asyncio.sleep(60)

# ... (بقية الملفات سليمة ولا تحتاج تعديل لأن منطق aiogram نفسه هو async)
# سأرفق لك نسخة نظيفة من `advanced_panel.py` و `panel.py` كمثال للتأكيد

async def startup_tasks(dp):
    try:
        await bot.send_message(ADMIN_CHAT_ID, "✅ **Bot is running (SYNC DB)!**")
        asyncio.create_task(schedule_channel_messages())
        # يمكنك إضافة مهمة process_scheduled_posts هنا إذا أردت
        print("✅ Background tasks started.")
    except Exception as e:
        print(f"STARTUP NOTIFICATION ERROR: {e}")
