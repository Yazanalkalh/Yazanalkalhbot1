from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
import data_store
from utils.helpers import forward_to_admin
from keyboards.inline.user_keyboards import create_user_buttons
import datetime
from config import ADMIN_CHAT_ID
from loader import bot
import hashlib

# This is the fully upgraded "Security Guard". It now understands
# Forced Subscription and Anti-Duplicate Message rules.

# A temporary, in-memory store for the last message fingerprint from each user
# In a larger bot, this might be moved to a more persistent cache like Redis
last_message_fingerprints = {}

def get_message_fingerprint(message: types.Message) -> str:
    """Creates a unique fingerprint for a message to detect duplicates."""
    if message.text:
        return hashlib.sha256(message.text.encode()).hexdigest()
    if message.sticker:
        return message.sticker.file_unique_id
    if message.photo:
        return message.photo[-1].file_unique_id
    if message.video:
        return message.video.file_unique_id
    if message.document:
        return message.document.file_unique_id
    # Fallback for other types
    return f"{message.chat.id}-{message.message_id}"


def is_not_admin(message: types.Message):
    """A filter to ensure the message is not from the admin."""
    return message.from_user.id != ADMIN_CHAT_ID

async def message_handler(message: types.Message, state: FSMContext):
    """Handler for all other user messages with advanced security checks."""
    user_id = message.from_user.id
    settings = data_store.bot_data.get('bot_settings', {})

    # --- NEW: Forced Subscription Check ---
    if settings.get('force_subscribe', False):
        channel_id = settings.get('force_channel_id')
        if channel_id:
            try:
                member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                if member.status not in ["creator", "administrator", "member"]:
                    channel_info = await bot.get_chat(channel_id)
                    invite_link = await channel_info.export_invite_link()
                    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("🔗 اضغط هنا للاشتراك", url=invite_link))
                    await message.reply("عذرًا, لاستخدام هذا البوت, يرجى الاشتراك أولاً في قناتنا.", reply_markup=keyboard)
                    return # Stop processing the message
            except Exception as e:
                print(f"Force Subscribe Error: Could not check membership for channel {channel_id}. Error: {e}")
    
    # --- NEW: Anti-Duplicate Message Check ---
    if settings.get('anti_duplicate_mode', False):
        fingerprint = get_message_fingerprint(message)
        last_fingerprint = last_message_fingerprints.get(user_id)
        if fingerprint == last_fingerprint:
            await message.reply("لقد استلمت هذه الرسالة منك للتو. سيتم تجاهلها.")
            return # Stop processing the message
        last_message_fingerprints[user_id] = fingerprint

    # --- Existing Checks (Unchanged) ---
    if user_id in data_store.bot_data.get('banned_users', []):
        return

    if message.text and message.text.strip() in data_store.bot_data.get('dynamic_replies', {}):
        reply_text = data_store.bot_data['dynamic_replies'][message.text.strip()]
        await message.reply(reply_text, reply_markup=create_user_buttons())
        return

    await forward_to_admin(message)
    await message.reply(
        settings.get('reply_message', "✅ تم استلام رسالتك بنجاح، شكراً لتواصلك."), 
        reply_markup=create_user_buttons()
    )

def register_message_handler(dp: Dispatcher):
    """Registers the handler for user messages."""
    dp.register_message_handler(message_handler, is_not_admin, state=None, content_types=types.ContentTypes.ANY)
