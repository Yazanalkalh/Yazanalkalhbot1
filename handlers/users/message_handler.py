from aiogram import types, Dispatcher
import data_store
from utils.helpers import forward_to_admin
from keyboards.inline.user_keyboards import create_user_buttons
import datetime
from config import ADMIN_CHAT_ID
from loader import bot # Import bot from loader

# This filter checks if the message sender is NOT the admin.
def is_not_admin(message: types.Message):
    """A filter to ensure the message is not from the admin."""
    return message.from_user.id != ADMIN_CHAT_ID

async def message_handler(message: types.Message):
    """Handler for all other user messages."""
    user_id = message.from_user.id
    settings = data_store.bot_data['bot_settings']

    # Ban Check
    if user_id in data_store.bot_data['banned_users']:
        return

    # Slow Mode & Spam are combined for simplicity
    slow_mode_seconds = settings.get('slow_mode_seconds', 0)
    if slow_mode_seconds > 0:
        last_msg_time = data_store.user_last_message_time.get(user_id)
        if last_msg_time and (datetime.datetime.now() - last_msg_time).total_seconds() < slow_mode_seconds:
            await message.reply(f"⏳ الرجاء الانتظار {slow_mode_seconds} ثواني بين الرسائل.")
            return
        data_store.user_last_message_time[user_id] = datetime.datetime.now()
    
    # Media Type Check
    allowed_media = settings.get('allowed_media_types', ['text'])
    if message.content_type not in allowed_media:
        await message.reply(settings.get('media_reject_message', "نوع الرسالة هذا غير مسموح به."))
        return

    # Dynamic Reply Check
    if message.text and message.text.strip() in data_store.bot_data['dynamic_replies']:
        reply_text = data_store.bot_data['dynamic_replies'][message.text.strip()]
        await message.reply(reply_text, reply_markup=create_user_buttons())
        return

    # If no dynamic reply, forward to admin and notify user
    await forward_to_admin(message) # No need to pass bot here anymore
    await message.reply(
        settings.get('reply_message', "✅ تم استلام رسالتك بنجاح، شكراً لتواصلك."), 
        reply_markup=create_user_buttons()
    )

def register_message_handler(dp: Dispatcher):
    """Registers the handler for user messages, ensuring it ignores the admin."""
    # This handler will now ONLY run for messages from non-admins.
    dp.register_message_handler(message_handler, is_not_admin, content_types=types.ContentTypes.ANY)
