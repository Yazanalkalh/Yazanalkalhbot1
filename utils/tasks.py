import asyncio
import datetime
import random
from loader import bot, dp
from config import ADMIN_CHAT_ID, CHANNEL_ID
import data_store

async def send_channel_message(custom_message=None):
    channel = data_store.bot_data.get("channel_id") or CHANNEL_ID
    if not channel:
        print("⚠️ النشر التلقائي متوقف: لم يتم تحديد قناة.")
        return

    message_to_send = custom_message or (random.choice(data_store.CHANNEL_MESSAGES) if data_store.CHANNEL_MESSAGES else None)
    if not message_to_send:
        print("⚠️ النشر التلقائي متوقف: لا توجد رسائل للنشر.")
        return

    try:
        await bot.send_message(channel, message_to_send)
        print(f"✅ تم إرسال رسالة تلقائية إلى القناة {channel}")
    except Exception as e:
        print(f"❌ فشل إرسال رسالة للقناة {channel}: {e}")

async def scheduled_tasks():
    while True:
        interval = data_store.bot_data.get("schedule_interval_seconds", 86400)
        await asyncio.sleep(interval)
        await send_channel_message()

async def startup_tasks(dispatcher):
    try:
        startup_message = (
            "✅ **تم تشغيل البوت بنجاح!**\n\n"
            "**الحالة:**\n"
            "- **البوت:** متصل ونشط\n"
            "- **قاعدة البيانات:** متصلة\n"
            "- **الخادم:** يعمل وجاهز\n\n"
            f"**وقت التشغيل:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await bot.send_message(ADMIN_CHAT_ID, startup_message)
    except Exception as e:
        print(f"⚠️ لم يتم إرسال رسالة بدء التشغيل للمشرف: {e}")
    
    asyncio.create_task(scheduled_tasks())
    print("🚀 تم جدولة المهام التلقائية بنجاح.")
