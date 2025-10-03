from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
import data_store
from utils.helpers import forward_to_admin
from keyboards.inline.user_keyboards import create_user_buttons
import datetime
from config import ADMIN_CHAT_ID
from loader import bot

# This filter ensures the message is NOT from the admin.
def is_not_admin(message: types.Message):
    """A filter to ensure the message is not from the admin."""
    return message.from_user.id != ADMIN_CHAT_ID

async def message_handler(message: types.Message, state: FSMContext):
    """Handler for all other user messages."""
    user_id = message.from_user.id
    settings = data_store.bot_data['bot_settings']

    # Ban Check
    if user_id in data_store.bot_data['banned_users']:
        return
    
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
    await forward_to_admin(message)
    await message.reply(
        settings.get('reply_message', "✅ تم استلام رسالتك بنجاح، شكراً لتواصلك."), 
        reply_markup=create_user_buttons()
    )

def register_message_handler(dp: Dispatcher):
    """
    Registers the handler for user messages.
    It will only trigger for users who are NOT the admin AND are not in any FSM state.
    """
    # --- THIS IS THE CRITICAL FIX ---
    # We add state=None to ensure this handler only runs for users not in a conversation.
    # This prevents it from intercepting admin commands.
    dp.register_message_handler(message_handler, is_not_admin, state=None, content_types=types.ContentTypes.ANY)
