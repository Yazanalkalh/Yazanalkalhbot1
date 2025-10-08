from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# ✅ تم الإصلاح: لا يوجد data_store هنا بعد الآن
from utils import database, texts, helpers
from keyboards.inline.user_keyboards import create_user_buttons
from config import ADMIN_CHAT_ID
from loader import bot
import hashlib

def get_message_fingerprint(message: types.Message) -> str:
    """Creates a unique fingerprint for a message to detect duplicates."""
    content = message.text or (message.sticker.file_unique_id if message.sticker else str(message.message_id))
    return hashlib.sha256(content.encode()).hexdigest()

def is_not_admin(message: types.Message):
    """A filter to ensure the message is not from the admin."""
    return message.from_user.id != ADMIN_CHAT_ID

async def message_handler(message: types.Message, state: FSMContext):
    """Handler for all other user messages with direct database checks."""
    user_id = message.from_user.id

    # --- 1. Maintenance Mode Check ---
    # ✅ تم الإصلاح: جلب إعداد واحد فقط وبشكل مباشر من قاعدة البيانات
    if database.get_setting("maintenance_mode", False):
        await message.reply(texts.get_text("user_maintenance_mode"))
        return
        
    # --- 2. Banned User Check ---
    # ✅ تم الإصلاح: فحص سريع ومباشر من قاعدة البيانات
    if database.is_user_banned(user_id):
        return # تجاهل المستخدم المحظور بصمت

    # --- 3. Forced Subscription Check ---
    if database.get_setting("force_subscribe", False):
        channel_id = database.get_setting("force_channel_id")
        if channel_id:
            try:
                member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                if member.status not in ["creator", "administrator", "member"]:
                    channel_info = await bot.get_chat(channel_id)
                    invite_link = await channel_info.export_invite_link() if not channel_info.invite_link else channel_info.invite_link
                    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("🔗 اضغط هنا للاشتراك", url=invite_link))
                    await message.reply(texts.get_text("user_force_subscribe"), reply_markup=keyboard)
                    return
            except Exception as e:
                print(f"Force Subscribe Error: {e}")

    # --- 4. Media Type Check ---
    allowed_media = database.get_setting('allowed_media_types', ['text'])
    if message.content_type not in allowed_media:
        reject_message = database.get_setting('media_reject_message', "عذرًا، هذا النوع من الرسائل غير مسموح به.")
        await message.reply(reject_message)
        return

    # --- 5. Anti-Duplicate Message Check (Now Persistent) ---
    if database.get_setting('anti_duplicate_mode', False):
        fingerprint = get_message_fingerprint(message)
        # ✅ تم الإصلاح: نقارن مع البصمة المحفوظة في قاعدة البيانات
        if database.get_user_last_fingerprint(user_id) == fingerprint:
            return # تجاهل بصمت
        # ✅ تم الإصلاح: نقوم بتحديث البصمة في قاعدة البيانات
        database.update_user_last_fingerprint(user_id, fingerprint)

    # --- 6. Dynamic Replies Check ---
    # ✅ تم الإصلاح: بحث مباشر عن الرد في قاعدة البيانات
    dynamic_reply = database.get_dynamic_reply(message.text)
    if dynamic_reply:
        await message.reply(dynamic_reply, reply_markup=create_user_buttons())
        return

    # --- Default Action: Forward to Admin ---
    await helpers.forward_to_admin(message)
    await message.reply(texts.get_text("user_default_reply"), reply_markup=create_user_buttons())

def register_message_handler(dp: Dispatcher):
    """Registers the handler for user messages."""
    dp.register_message_handler(
        message_handler, is_not_admin, 
        lambda message: message.chat.type == types.ChatType.PRIVATE,
        state=None, content_types=types.ContentTypes.ANY
    )
