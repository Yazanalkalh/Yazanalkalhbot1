import asyncio
import datetime
import random
from loader import bot
from config import ADMIN_CHAT_ID
from utils.helpers import bot_data, CHANNEL_MESSAGES, start_time

async def send_channel_message(custom_message=None):
    """يرسل رسالة عشوائية أو مخصصة للقناة المحددة."""
    channel_id = bot_data.get("channel_id")
    if not channel_id:
        print("⚠️ النشر التلقائي متوقف: معرف القناة غير محدد.")
        return False
    
    if not CHANNEL_MESSAGES and not custom_message:
        print("⚠️ النشر التلقائي متوقف: لا توجد رسائل للنشر.")
        return False
    
    try:
        message_to_send = custom_message or random.choice(CHANNEL_MESSAGES)
        await bot.send_message(chat_id=channel_id, text=message_to_send)
        print(f"✅ تم إرسال رسالة بنجاح إلى القناة {channel_id}")
        return True
    except Exception as e:
        print(f"❌ خطأ في إرسال الرسالة للقناة: {e}")
        return False

async def schedule_channel_messages():
    """جدولة الرسائل التلقائية للقناة بناءً على الفترة المحددة."""
    print("⏳ بدء جدولة الرسائل التلقائية للقناة...")
    while True:
        try:
            interval_seconds = bot_data.get("schedule_interval_seconds", 86400)
            await asyncio.sleep(interval_seconds)
            await send_channel_message()
        except Exception as e:
            print(f"❌ خطأ فادح في حلقة جدولة الرسائل: {e}")
            await asyncio.sleep(60)

async def startup_tasks(dp):
    """
    الدالة التي يتم تشغيلها عند بدء تشغيل البوت.
    تقوم بإرسال رسالة تأكيد للمشرف وبدء المهام الخلفية.
    """
    try:
        startup_message = (
            "✅ **البوت يعمل الآن بنجاح**\n\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            "🤖 **الحالة:** متصل وجاهز\n"
            "🌐 **خادم الويب:** يعمل\n"
            "☁️ **قاعدة البيانات:** متصلة\n"
            "📱 **استقبال الرسائل:** مفعل\n"
            f"⏰ **وقت البدء:** {start_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await bot.send_message(ADMIN_CHAT_ID, startup_message, parse_mode="Markdown")
        
        asyncio.create_task(schedule_channel_messages())
        print("✅ البوت جاهز للعمل. تم تفعيل المهام الخلفية.")

    except Exception as e:
        print(f"❌ خطأ في دالة بدء التشغيل (startup): {e}")


