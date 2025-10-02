from aiogram import Dispatcher, types
from loader import bot
from config import ADMIN_CHAT_ID
from utils.helpers import (
    is_banned, check_spam_limit, get_spam_warning_message, create_buttons,
    get_hijri_date, get_live_time, get_daily_reminder, handle_user_content,
    USERS_LIST, bot_data, save_data, AUTO_REPLIES
)

async def send_welcome(message: types.Message):
    """Handler for the /start command."""
    if is_banned(message.from_user.id): return
    user_id = message.from_user.id
    if user_id not in USERS_LIST:
        USERS_LIST.add(user_id)
        bot_data["users"] = list(USERS_LIST)
        save_data(bot_data)
    user_name = message.from_user.first_name or "عزيزي المستخدم"
    custom_welcome = bot_data.get("welcome_message")
    if custom_welcome:
        welcome_text = custom_welcome.replace("{name}", user_name)
    else:
        welcome_text = (f"👋 أهلًا وسهلًا بك، {user_name}!\nهذا البوت مخصص للإجابة عن استفساراتك حول القناة...")
    await message.reply(welcome_text, reply_markup=create_buttons(), parse_mode="Markdown")

async def handle_user_message(message: types.Message):
    """Handles text messages from users."""
    if is_banned(message.from_user.id): return
    spam_allowed, spam_status = check_spam_limit(message.from_user.id)
    if not spam_allowed:
        await message.reply(get_spam_warning_message(spam_status, message.from_user.first_name))
        return
    user_message = message.text.strip()
    if user_message in AUTO_REPLIES:
        await message.reply(AUTO_REPLIES[user_message], reply_markup=create_buttons())
        return
    await handle_user_content(message, user_message)
    custom_reply = bot_data.get("reply_message") or "🌿 تم الاستلام بنجاح! جزاك الله خيرًا على تواصلك."
    await message.reply(custom_reply, reply_markup=create_buttons())

async def handle_media_message(message: types.Message):
    """Handles non-text content from users and rejects it if not allowed."""
    if is_banned(message.from_user.id): return
    if not bot_data.get("allow_media", False):
        await message.reply(bot_data.get("media_reject_message"))
        bot_data["rejected_media_count"] = bot_data.get("rejected_media_count", 0) + 1
        save_data(bot_data)
        return
    await handle_user_content(message, "[وسائط]")

async def process_callback(callback_query: types.CallbackQuery):
    """Handles callbacks from the main menu buttons."""
    if is_banned(callback_query.from_user.id):
        await bot.answer_callback_query(callback_query.id, "❌ أنت محظور!")
        return
    await bot.answer_callback_query(callback_query.id)
    data = callback_query.data
    user_id = callback_query.from_user.id
    if data == "hijri_today":
        await bot.send_message(user_id, get_hijri_date())
    elif data == "live_time":
        await bot.send_message(user_id, get_live_time())
    elif data == "daily_reminder":
        await bot.send_message(user_id, get_daily_reminder())
    elif data == "from_developer":
        await bot.send_message(user_id, "تم تطوير هذا البوت بواسطة ✨ ابو سيف بن ذي يزن ✨\n[فريق التقويم الهجري](https://t.me/HejriCalender)", parse_mode="Markdown")

def register_user_handlers(dp: Dispatcher):
    """Registers all user-facing handlers."""
    dp.register_message_handler(send_welcome, commands=['start'], state="*")
    dp.register_message_handler(handle_media_message, lambda m: m.from_user.id != ADMIN_CHAT_ID, content_types=types.ContentTypes.ANY, state="*")
    # The text handler is now part of ANY content type, so we don't register it separately to avoid conflicts. Logic is inside handle_media_message.
    dp.register_callback_query_handler(process_callback, lambda c: c.from_user.id != ADMIN_CHAT_ID, state="*")



