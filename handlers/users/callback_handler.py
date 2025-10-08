from aiogram import types, Dispatcher
from loader import bot
# ✅ تم الإصلاح: لا يوجد data_store، نستخدم قاعدة البيانات مباشرة
from utils import database
from utils.helpers import get_hijri_date_str, get_live_time_str, get_random_reminder

async def callback_query_handler(cq: types.CallbackQuery):
    """
    ✅ تم الإصلاح: هذا المعالج الآن يتحقق من الحظر ويطبق الإعدادات مباشرة من قاعدة البيانات.
    """
    # 1. فحص الحظر المباشر والآمن من قاعدة البيانات
    if await database.is_user_banned(cq.from_user.id):
        await cq.answer("🚫 أنت محظور من استخدام البوت.", show_alert=True)
        return

    await cq.answer()
    
    response_text = ""
    if cq.data == "show_date":
        response_text = get_hijri_date_str()
    elif cq.data == "show_time":
        response_text = get_live_time_str()
    elif cq.data == "show_reminder":
        response_text = get_random_reminder()
    
    if response_text:
        try:
            # 2. جلب إعداد حماية المحتوى المحدث مباشرة من قاعدة البيانات
            bot_settings = await database.get_setting('bot_settings', {})
            protect = bot_settings.get('content_protection', False)
            
            await bot.send_message(
                chat_id=cq.from_user.id, 
                text=response_text,
                protect_content=protect
            )
        except Exception as e:
            print(f"Error sending callback response: {e}")

def register_callback_handler(dp: Dispatcher):
    """(لا تغييرات هنا، هذه الدالة سليمة)"""
    dp.register_callback_query_handler(callback_query_handler, state=None)
