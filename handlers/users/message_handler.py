from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
import data_store
from utils.helpers import forward_to_admin
from keyboards.inline.user_keyboards import create_user_buttons
import datetime
from config import ADMIN_CHAT_ID
from loader import bot

# This is the correct filter name.
def is_not_admin(message: types.Message):
    """A filter to ensure the message is not from the admin."""
    return message.from_user.id != ADMIN_CHAT_ID

async def message_handler(message: types.Message, state: FSMContext):
    """Handler for all other user messages."""
    user_id = message.from_user.id
    settings = data_store.bot_data['bot_settings']

    if user_id in data_store.bot_data['banned_users']:
        return
    
    if message.content_type not in settings.get('allowed_media_types', ['text']):
        await message.reply(settings.get('media_reject_message', "نوع الرسالة هذا غير مسموح به."))
        return

    if message.text and message.text.strip() in data_store.bot_data['dynamic_replies']:
        await message.reply(data_store.bot_data['dynamic_replies'][message.text.strip()], reply_markup=create_user_buttons())
        return

    await forward_to_admin(message)
    await message.reply(settings.get('reply_message', "✅ تم استلام رسالتك بنجاح، شكراً لتواصلك."), reply_markup=create_user_buttons())

def register_message_handler(dp: Dispatcher):
    """Registers the handler for user messages."""
    dp.register_message_handler(message_handler, is_not_admin, state=None, content_types=types.ContentTypes.ANY)
