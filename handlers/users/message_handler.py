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

# This is the final and definitive version of the "Security Guard".

last_message_fingerprints = {}

def get_message_fingerprint(message: types.Message) -> str:
    content = message.text or (message.sticker.file_unique_id if message.sticker else str(message.message_id))
    return hashlib.sha256(content.encode()).hexdigest()

def is_not_admin(message: types.Message):
    return message.from_user.id != ADMIN_CHAT_ID

async def message_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    settings = data_store.bot_data.get('bot_settings', {})

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
                    invite_link = (await bot.get_chat(channel_id)).invite_link or await bot.export_chat_invite_link(channel_id)
                    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔗 اضغط هنا للاشتراك", url=invite_link))
                    await message.reply("عذرًا, لاستخدام البوت, يرجى الاشتراك أولاً في قناتنا.", reply_markup=kb)
                    return
            except Exception as e:
                print(f"Force Subscribe Error: {e}")

    # --- 3. Anti-Duplicate Message Check ---
    if settings.get('anti_duplicate_mode', False):
        fingerprint = get_message_fingerprint(message)
        if last_message_fingerprints.get(user_id) == fingerprint:
            return # Silently ignore
        last_message_fingerprints[user_id] = fingerprint

    # --- Existing Logic ---
    if user_id in data_store.bot_data.get('banned_users', []): return

    if message.text and message.text.strip() in data_store.bot_data.get('dynamic_replies', {}):
        await message.reply(data_store.bot_data['dynamic_replies'][message.text.strip()], reply_markup=create_user_buttons())
        return

    await forward_to_admin(message)
    await message.reply(settings.get('reply_message', "✅ تم استلام رسالتك."), reply_markup=create_user_buttons())

def register_message_handler(dp: Dispatcher):
    dp.register_message_handler(
        message_handler, is_not_admin, 
        lambda message: message.chat.type == types.ChatType.PRIVATE,
        state=None, content_types=types.ContentTypes.ANY
    )
