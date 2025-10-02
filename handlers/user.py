from aiogram import types, Dispatcher
from data_store import bot_data, USERS_LIST, AUTO_REPLIES, save_all_data
from utils.helpers import is_banned, get_hijri_date, get_live_time, get_daily_reminder, forward_to_admin
from keyboards.inline import create_user_buttons # استدعاء الأزرار من الملف الجديد
from config import ADMIN_CHAT_ID

async def send_welcome(message: types.Message):
    if is_banned(message.from_user.id): return
    user_id = message.from_user.id
    if user_id not in USERS_LIST:
        USERS_LIST.add(user_id)
        save_all_data()

    user_name = message.from_user.first_name
    welcome = bot_data.get("welcome_message", "").format(name=user_name) or f"👋 **أهلاً بك، {user_name}!**\n\nهذا البوت مخصص للتواصل مع فريق القناة. أرسل استفسارك وسيتم الرد عليك."
    await message.reply(welcome, reply_markup=create_user_buttons())

async def handle_user_message(message: types.Message):
    if is_banned(message.from_user.id): return
    if message.text and message.text in AUTO_REPLIES:
        await message.reply(AUTO_REPLIES[message.text], reply_markup=create_user_buttons())
        return

    await forward_to_admin(message)
    reply = bot_data.get("reply_message") or "✅ **تم استلام رسالتك!** سيقوم الفريق بمراجعتها والرد عليك."
    await message.reply(reply, reply_markup=create_user_buttons())

async def handle_media(message: types.Message):
    if is_banned(message.from_user.id): return
    if not bot_data.get("allow_media", False):
        await message.reply(bot_data.get("media_reject_message"))
        return
    await forward_to_admin(message)
    reply = bot_data.get("reply_message") or "✅ **تم استلام رسالتك!**"
    await message.reply(reply, reply_markup=create_user_buttons())

async def process_callback(call: types.CallbackQuery):
    if is_banned(call.from_user.id):
        await call.answer("❌ أنت محظور.", show_alert=True)
        return
    
    await call.answer()
    responses = {
        "hijri_today": get_hijri_date(),
        "live_time": get_live_time(),
        "daily_reminder": get_daily_reminder()
    }

    if call.data in responses:
        await call.message.answer(responses[call.data], parse_mode="Markdown", disable_web_page_preview=True)

def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(send_welcome, commands=['start'], state="*")
    dp.register_message_handler(handle_user_message, lambda m: m.from_user.id != ADMIN_CHAT_ID, content_types=types.ContentTypes.TEXT, state="*")
    dp.register_message_handler(handle_media, lambda m: m.from_user.id != ADMIN_CHAT_ID, content_types=types.ContentTypes.ANY, state="*")
    dp.register_callback_query_handler(process_callback, lambda c: c.from_user.id != ADMIN_CHAT_ID, state="*")
