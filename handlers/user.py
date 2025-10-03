import time
from aiogram import types, Dispatcher
import data_store
from utils.helpers import is_banned, get_hijri_date, get_live_time, get_daily_reminder, forward_to_admin, process_klisha
from keyboards.inline import create_user_buttons
from config import ADMIN_CHAT_ID

async def check_maintenance(message: types.Message):
    settings = data_store.bot_data['bot_settings']
    if settings.get('maintenance_mode', False):
        await message.reply(settings.get('maintenance_message'))
        return True
    return False

async def check_slow_mode(message: types.Message):
    settings = data_store.bot_data['bot_settings']
    slow_mode_seconds = settings.get('slow_mode_seconds', 0)
    if slow_mode_seconds > 0:
        user_id = message.from_user.id
        current_time = time.time()
        last_time = data_store.user_last_message_time.get(user_id, 0)
        if current_time - last_time < slow_mode_seconds:
            await message.reply(f"⏳ الرجاء الانتظار {slow_mode_seconds} ثواني بين الرسائل.")
            return True
        data_store.user_last_message_time[user_id] = current_time
    return False

async def send_welcome(message: types.Message):
    if await check_maintenance(message): return
    if is_banned(message.from_user.id): return
    
    user_id = message.from_user.id
    if user_id not in data_store.bot_data['users']:
        data_store.bot_data['users'].append(user_id)
        data_store.save_data()

    raw_welcome = data_store.bot_data['bot_settings'].get("welcome_message")
    processed_welcome = process_klisha(raw_welcome, message.from_user)
    await message.reply(processed_welcome, reply_markup=create_user_buttons(), parse_mode="HTML",
                        protect_content=data_store.bot_data['bot_settings'].get('content_protection'))

async def handle_any_message(message: types.Message):
    if await check_maintenance(message): return
    if is_banned(message.from_user.id): return
    if await check_slow_mode(message): return

    # Check for dynamic replies first
    if message.text and message.text in data_store.bot_data['dynamic_replies']:
        await message.reply(data_store.bot_data['dynamic_replies'][message.text], 
                            reply_markup=create_user_buttons(),
                            protect_content=data_store.bot_data['bot_settings'].get('content_protection'))
        return

    # Check media type
    allowed_types = data_store.bot_data['bot_settings'].get('allowed_media_types', ['text'])
    if message.content_type not in allowed_types:
        await message.reply(data_store.bot_data['bot_settings'].get("media_reject_message"))
        return

    # If all checks pass, forward to admin and send confirmation
    await forward_to_admin(message)
    reply_text = data_store.bot_data['bot_settings'].get("reply_message")
    await message.reply(reply_text, reply_markup=create_user_buttons(),
                        protect_content=data_store.bot_data['bot_settings'].get('content_protection'))

async def process_callback(call: types.CallbackQuery):
    if await check_maintenance(call.message): return
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
        await call.message.answer(responses[call.data], disable_web_page_preview=True,
                                  protect_content=data_store.bot_data['bot_settings'].get('content_protection'))

def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(send_welcome, commands=['start'], state="*")
    # A single handler for all other user messages
    dp.register_message_handler(handle_any_message, 
                                lambda m: m.from_user.id != ADMIN_CHAT_ID, 
                                content_types=types.ContentTypes.ANY, 
                                state="*")
    dp.register_callback_query_handler(process_callback, 
                                       lambda c: c.from_user.id != ADMIN_CHAT_ID, 
                                       state="*")
