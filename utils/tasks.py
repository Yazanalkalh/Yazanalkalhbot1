import asyncio
import datetime
import random
from loader import bot
from config import ADMIN_CHAT_ID, CHANNEL_ID
from utils.helpers import bot_data, CHANNEL_MESSAGES

async def send_channel_message(custom_message=None):
    """
    يرسل رسالة عشوائية أو محددة إلى القناة.
    """
    channel_id = bot_data.get("channel_id") or CHANNEL_ID
    if not channel_id:
        print("❌ معرف القناة غير محدد في الإعدادات.")
        return False

    if not CHANNEL_MESSAGES and not custom_message:
        print("❌ لا توجد رسائل متاحة للنشر في القناة.")
        return False

    try:
        message = custom_message or random.choice(CHANNEL_MESSAGES)
        if not channel_id.startswith('@') and not channel_id.startswith('-'):
            channel_id = '@' + channel_id
        await bot.send_message(chat_id=channel_id, text=message)
        print(f"✅ تم إرسال رسالة للقناة: {channel_id}")
        return True
    except Exception as e:
        print(f"❌ خطأ في إرسال الرسالة للقناة: {e}")
        return False

async def schedule_channel_messages():
    """
    مهمة خلفية لجدولة إرسال الرسائل للقناة بشكل دوري.
    """
    print("🕐 بدء جدولة الرسائل التلقائية للقناة...")
    while True:
        try:
            interval = bot_data.get("schedule_interval_seconds", 86400)
            print(f"⏰ انتظار {interval // 3600} ساعة حتى الرسالة المجدولة التالية...")
            await asyncio.sleep(interval)

            if (bot_data.get("channel_id") or CHANNEL_ID) and CHANNEL_MESSAGES:
                await send_channel_message()

        except Exception as e:
            print(f"❌ خطأ في جدولة الرسائل: {e}")
            await asyncio.sleep(60) # الانتظار لمدة دقيقة قبل المحاولة مرة أخرى عند حدوث خطأ

async def keep_alive_task():
    """
    مهمة خلفية للتأكد من أن البوت لا يزال متصلاً.
    """
    print("🔄 بدء مهمة إبقاء البوت نشطًا...")
    while True:
        await asyncio.sleep(1800)  # كل 30 دقيقة
        try:
            me = await bot.get_me()
            print(f"🔄 البوت لا يزال نشطًا: @{me.username} - {datetime.datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"⚠️ تحذير في مهمة إبقاء البوت نشطًا: {e}")

async def startup_tasks():
    """
    هذه هي الدالة المفقودة التي تجمع كل المهام الخلفية لتبدأ مع البوت.
    """
    print("🚀 إنشاء المهام الخلفية...")
    asyncio.create_task(schedule_channel_messages())
    asyncio.create_task(keep_alive_task())
