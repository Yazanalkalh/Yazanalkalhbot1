import asyncio
import random
from loader import bot
from config import ADMIN_CHAT_ID
# ✅ تم الإصلاح: لا يوجد data_store هنا
from utils import database

async def schedule_channel_messages():
    """
    ✅ تم الإصلاح: هذه الدالة الآن تقرأ الإعدادات مباشرة من قاعدة البيانات في كل دورة.
    """
    while True:
        try:
            # نقوم بجلب الإعدادات المحدثة مباشرة قبل استخدامها
            interval = database.get_setting('schedule_interval_seconds', 86400)
            await asyncio.sleep(interval)

            channel_id = database.get_setting('channel_id')
            # نستخدم دالة جديدة لجلب الرسائل من قاعدة البيانات
            messages = database.get_channel_messages()

            if channel_id and messages:
                message_text = random.choice(messages)
                await bot.send_message(channel_id, message_text)
                print(f"✅ Auto-posted random message to channel {channel_id}")
        except Exception as e:
            print(f"CHANNEL SCHEDULER ERROR: {e}")
            await asyncio.sleep(60)

async def process_scheduled_posts():
    """
    ✅ تم الإصلاح: هذه الدالة الآن تقرأ إعدادات الإشعارات مباشرة من قاعدة البيانات.
    """
    while True:
        try:
            await asyncio.sleep(30)
            
            due_posts = database.get_due_scheduled_posts()
            if not due_posts:
                continue

            # نقوم بجلب إعدادات الإشعارات قبل البدء بالمعالجة
            notify_on_success = database.get_setting('notification_on_success', False)
            notify_on_fail = database.get_setting('notification_on_fail', False)

            for post in due_posts:
                content_doc = database.get_content_from_library(post['content_id'])
                channel_id_to_post = post.get('channel_id', 'N/A')

                try:
                    if not content_doc:
                        raise ValueError(f"المحتوى ID {post['content_id']} لم يعد موجودًا في المكتبة.")

                    content_type = content_doc['type']
                    content_value = content_doc['value']

                    if content_type == 'text':
                        await bot.send_message(channel_id_to_post, content_value)
                    # ... (أضف أنواع محتوى أخرى هنا إذا لزم الأمر)

                    database.mark_post_as_sent(post['_id'])
                    print(f"✅ Sent scheduled {content_type} to {channel_id_to_post}")

                    if notify_on_success:
                        await bot.send_message(ADMIN_CHAT_ID, f"✅ **إشعار نجاح**\n\nتم نشر المحتوى المجدول بنجاح في القناة `{channel_id_to_post}`.")

                except Exception as e:
                    print(f"SCHEDULED POST SEND ERROR for post {post['_id']}: {e}")
                    if notify_on_fail:
                        error_message = str(e)
                        await bot.send_message(
                            ADMIN_CHAT_ID,
                            f"⚠️ **إشعار فشل**\n\nفشلت في نشر المحتوى المجدول في القناة `{channel_id_to_post}`.\n\n"
                            f"**سبب الخطأ:**\n`{error_message}`"
                        )
        except Exception as e:
            print(f"MAJOR SCHEDULED POST PROCESSOR ERROR: {e}")
            await asyncio.sleep(60)


async def startup_tasks(dp):
    """(لا تغييرات هنا، هذه الدالة سليمة)"""
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
