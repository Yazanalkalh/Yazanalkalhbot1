import asyncio
import random
from loader import bot
from config import ADMIN_CHAT_ID
# ✅ تم التحديث: استيراد قاعدة البيانات مباشرة
from utils import database

# --- ✅ تم الإصلاح: هذه الدالة الآن محصنة ضد الانهيار ---
async def schedule_channel_messages():
    """يرسل بشكل دوري رسالة عشوائية من قائمة رسائل القناة."""
    while True:
        try:
            # نقرأ الإعدادات مباشرة من قاعدة البيانات
            interval = await database.get_setting("schedule_interval_seconds", 86400)
            await asyncio.sleep(interval)

            channel_id = await database.get_setting("channel_id")
            messages = await database.get_all_channel_messages() # هذه هي القائمة التي قد تكون فارغة

            # 🔴 هذا هو الإصلاح: نتأكد من أن القناة موجودة وأن هناك رسائل لإرسالها
            if channel_id and messages:
                message_text = random.choice(messages)
                await bot.send_message(channel_id, message_text)
                print(f"✅ Auto-posted random message to channel {channel_id}")

        except Exception as e:
            print(f"CHANNEL SCHEDULER ERROR: {e}")
            # ننتظر قليلاً قبل المحاولة مرة أخرى في حالة حدوث خطأ
            await asyncio.sleep(60)


async def process_scheduled_posts():
    """
    (لا تغيير هنا، هذه الدالة سليمة ومحصنة بالفعل)
    """
    while True:
        try:
            await asyncio.sleep(30) # يتحقق كل 30 ثانية
            
            due_posts = await database.get_due_scheduled_posts()
            if not due_posts:
                continue

            # نقرأ إعدادات الإشعارات مباشرة من قاعدة البيانات
            notify_on_success = await database.get_setting("notification_on_success", False)
            notify_on_fail = await database.get_setting("notification_on_fail", False)

            for post in due_posts:
                content_doc = await database.get_content_from_library(post['content_id'])
                channel_id_to_post = post.get('channel_id', 'N/A')

                try:
                    if not content_doc:
                        raise ValueError(f"المحتوى ID {post['content_id']} لم يعد موجودًا في المكتبة.")

                    content_type = content_doc['type']
                    content_value = content_doc['value']

                    if content_type == 'text':
                        await bot.send_message(channel_id_to_post, content_value)
                    # يمكنك إضافة المزيد من الأنواع هنا لاحقًا (photo, sticker, etc.)
                    
                    await database.mark_post_as_sent(post['_id'])
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
                            f"**سبب الخطأ:**\n`{error_message}`\n\n"
                            "سيحاول البوت إعادة الإرسال في الدورة التالية."
                        )

        except Exception as e:
            print(f"MAJOR SCHEDULED POST PROCESSOR ERROR: {e}")
            await asyncio.sleep(60)


async def startup_tasks(dp):
    """(لا تغيير هنا، هذه الدالة سليمة)"""
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
