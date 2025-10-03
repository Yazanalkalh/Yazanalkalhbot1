from aiogram import types, Dispatcher
import data_store
from utils.helpers import is_banned, get_hijri_date, get_live_time, get_daily_reminder, forward_to_admin, process_klisha
from keyboards.inline import create_user_buttons
from config import ADMIN_CHAT_ID

async def send_welcome(message: types.Message):
    if is_banned(message.from_user.id): return
    user_id = message.from_user.id
    if user_id not in data_store.bot_data['users']:
        data_store.bot_data['users'].append(user_id)
        data_store.save_data()

    raw_welcome = data_store.bot_data['bot_config'].get("welcome_message")
    processed_welcome = process_klisha(raw_welcome, message.from_user)
    await message.reply(processed_welcome, reply_markup=create_user_buttons(), parse_mode="HTML")

async def handle_user_message(message: types.Message):
    if is_banned(message.from_user.id): return

    # البحث في الردود الديناميكية
    if message.text and message.text in data_store.bot_data['dynamic_replies']:
        await message.reply(data_store.bot_data['dynamic_replies'][message.text], reply_markup=create_user_buttons())
        return

    # إذا لم يتم العثور على رد، أرسل للمشرف
    await forward_to_admin(message)
    reply_text = data_store.bot_data['bot_config'].get("reply_message")
    await message.reply(reply_text, reply_markup=create_user_buttons())

async def handle_media(message: types.Message):
    if is_banned(message.from_user.id): return
    if not data_store.bot_data['bot_config'].get("allow_media", False):
        await message.reply(data_store.bot_data['bot_config'].get("media_reject_message"))
        return
    await forward_to_admin(message)
    reply_text = data_store.bot_data['bot_config'].get("reply_message")
    await message.reply(reply_text, reply_markup=create_user_buttons())

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
        await call.message.answer(responses[call.data], disable_web_page_preview=True)

def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(send_welcome, commands=['start'], state="*")
    dp.register_message_handler(handle_user_message, lambda m: m.from_user.id != ADMIN_CHAT_ID, content_types=types.ContentTypes.TEXT, state="*")
    dp.register_message_handler(handle_media, lambda m: m.from_user.id != ADMIN_CHAT_ID, content_types=types.ContentTypes.ANY, state="*")
    dp.register_callback_query_handler(process_callback, lambda c: c.from_user.id != ADMIN_CHAT_ID, state="*")
