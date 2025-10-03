import datetime
from aiogram import types, Dispatcher
from loader import bot
import data_store
from utils.helpers import forward_to_admin
from keyboards.inline.user_keyboards import create_user_buttons
import config

async def message_handler(message: types.Message):
    """Handler for all other user messages."""
    user_id = message.from_user.id
    settings = data_store.bot_data.get('bot_settings', {})

    if settings.get('maintenance_mode', False) and user_id != config.ADMIN_CHAT_ID:
        await message.reply(settings.get('maintenance_message', "البوت في الصيانة."))
        return

    if user_id in data_store.bot_data.get('banned_users', []):
        return

    slow_mode_seconds = settings.get('slow_mode_seconds', 0)
    if slow_mode_seconds > 0:
        last_msg_time = data_store.user_last_message_time.get(user_id)
        if last_msg_time and (datetime.datetime.now() - last_msg_time).total_seconds() < slow_mode_seconds:
            await message.reply(f"⏳ الرجاء الانتظار {slow_mode_seconds} ثواني بين الرسائل.")
            return
        data_store.user_last_message_time[user_id] = datetime.datetime.now()
    
    allowed_media = settings.get('allowed_media_types', ['text'])
    if message.content_type not in allowed_media:
        await message.reply(settings.get('media_reject_message', "نوع الرسالة هذا غير مسموح به."))
        return

    if message.text and message.text.strip() in data_store.bot_data.get('dynamic_replies', {}):
        reply_text = data_store.bot_data['dynamic_replies'][message.text.strip()]
        await message.reply(reply_text, reply_markup=create_user_buttons())
        return

    await forward_to_admin(message, bot)
    await message.reply(
        settings.get('reply_message', "تم استلام رسالتك."), 
        reply_markup=create_user_buttons()
    )

def register_message_handlers(dp: Dispatcher):
    # This handler should be registered last to act as a catch-all
    dp.register_message_handler(message_handler, content_types=types.ContentTypes.ANY)
