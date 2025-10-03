import asyncio
import datetime
from loader import bot
import data_store
from config import ADMIN_CHAT_ID

async def schedule_auto_posts():
    """المهمة الخلفية لإرسال المنشورات التلقائية للقناة."""
    print("🔄 Starting auto-post scheduler...")
    while True:
        interval = data_store.bot_data['bot_config'].get('schedule_interval_seconds', 86400)
        await asyncio.sleep(interval)
        
        channel_id = data_store.bot_data['bot_config'].get('channel_id')
        messages = data_store.bot_data.get('channel_messages', [])
        
        if channel_id and messages:
            try:
                await bot.send_message(channel_id, random.choice(messages))
                print(f"✅ Auto-posted to channel {channel_id}")
            except Exception as e:
                print(f"❌ Failed to auto-post to channel: {e}")

async def schedule_specific_posts():
    """المهمة الخلفية لإرسال المنشورات المجدولة المتقدمة."""
    print("🔄 Starting specific-post scheduler...")
    while True:
        await asyncio.sleep(60) # يفحص كل دقيقة
        now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        
        posts_to_send = []
        remaining_posts = []

        for post in data_store.bot_data.get("scheduled_posts", []):
            send_time = datetime.datetime.fromisoformat(post['send_at_iso'])
            if now >= send_time:
                posts_to_send.append(post)
            else:
                remaining_posts.append(post)
        
        if posts_to_send:
            for post in posts_to_send:
                try:
                    await bot.send_message(post['channel_id'], post['text'])
                    print(f"✅ Sent scheduled post to {post['channel_id']}")
                except Exception as e:
                    print(f"❌ Failed to send scheduled post: {e}")
            
            # تحديث قائمة المنشورات في قاعدة البيانات
            data_store.bot_data["scheduled_posts"] = remaining_posts
            data_store.save_data()

async def startup_tasks(dp):
    """
    مجموعة المهام التي تبدأ مع تشغيل البوت.
    """
    asyncio.create_task(schedule_auto_posts())
    asyncio.create_task(schedule_specific_posts())
    try:
        startup_message = (
            "✅ **تم تشغيل البوت بنجاح!**\n\n"
            "🤖 **الحالة:** متصل ونشط\n"
            "🌐 **خادم الويب:** يعمل\n"
            "☁️ **قاعدة البيانات:** متصلة\n"
            f"⏰ **وقت التشغيل:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await bot.send_message(ADMIN_CHAT_ID, startup_message)
    except Exception as e:
        print(f"⚠️ Could not send startup message to admin: {e}")
