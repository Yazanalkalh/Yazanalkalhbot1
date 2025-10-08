from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import data_store
from utils.helpers import forward_to_admin
from keyboards.inline.user_keyboards import create_user_buttons
import datetime
from config import ADMIN_CHAT_ID
from loader import bot
import hashlib
# --- NEW: Import the function to get the latest data directly ---
from utils.database import load_db_data

# This is the final, definitive version of the "Security Guard".
# It now fetches the latest settings from the database on every message.

last_message_fingerprints = {}

def get_message_fingerprint(message: types.Message) -> str:
    """Creates a unique fingerprint for a message to detect duplicates."""
    content = message.text or (message.sticker.file_unique_id if message.sticker else str(message.message_id))
    return hashlib.sha256(content.encode()).hexdigest()

def is_not_admin(message: types.Message):
    """A filter to ensure the message is not from the admin."""
    return message.from_user.id != ADMIN_CHAT_ID

async def message_handler(message: types.Message, state: FSMContext):
    """Handler for all other user messages with advanced security checks."""
    user_id = message.from_user.id
    
    # --- THIS IS THE CRITICAL FIX ---
    # Instead of using the old in-memory data, we fetch the LATEST data from the DB on every message.
    # This ensures that any change made by the admin is applied instantly.
    bot_data = load_db_data()
    settings = bot_data.get('bot_settings', {})
    # --------------------------------

    # --- 1. Maintenance Mode Check ---
    if settings.get('maintenance_mode', False):
        await message.reply(settings.get('maintenance_message', "عذرًا، البوت قيد الصيانة حاليًا."))
        return

    # --- 2. Forced Subscription Check ---
    if settings.get('force_subscribe', False):
        channel_id = settings.get('force_channel_id')
        if channel_id:
            try:
                member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                if member.status not in ["creator", "administrator", "member"]:
                    channel_info = await bot.get_chat(channel_id)
                    invite_link = await channel_info.export_invite_link() if not channel_info.invite_link else channel_info.invite_link
                    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("🔗 اضغط هنا للاشتراك", url=invite_link))
                    await message.reply("عذرًا, لاستخدام هذا البوت, يرجى الاشتراك أولاً في قناتنا.", reply_markup=keyboard)
                    return
            except Exception as e:
                print(f"Force Subscribe Error: {e}")

    # --- 3. Anti-Duplicate Message Check ---
    if settings.get('anti_duplicate_mode', False):
        fingerprint = get_message_fingerprint(message)
        if last_message_fingerprints.get(user_id) == fingerprint:
            return # Silently ignore
        last_message_fingerprints[user_id] = fingerprint

    # --- Existing Logic (now uses up-to-date data) ---
    if user_id in bot_data.get('banned_users', []): return

    if message.text and message.text.strip() in bot_data.get('dynamic_replies', {}):
        await message.reply(bot_data['dynamic_replies'][message.text.strip()], reply_markup=create_user_buttons())
        return

    await forward_to_admin(message)
    await message.reply(settings.get('reply_message', "✅ تم استلام رسالتك بنجاح، شكراً لتواصلك."), reply_markup=create_user_buttons())

def register_message_handler(dp: Dispatcher):
    """Registers the handler for user messages."""
    dp.register_message_handler(
        message_handler, is_not_admin, 
        lambda message: message.chat.type == types.ChatType.PRIVATE,
        state=None, content_types=types.ContentTypes.ANY
    )
