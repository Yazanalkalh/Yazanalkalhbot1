from aiogram import types, Dispatcher
from loader import bot
import data_store
from utils.helpers import get_hijri_date_str, get_live_time_str, get_random_reminder, format_welcome_message, forward_to_admin
from keyboards.inline import create_user_buttons
import datetime

async def start_cmd(message: types.Message):
    """Handler for the /start command."""
    user_id = message.from_user.id
    if user_id not in data_store.bot_data['users']:
        data_store.bot_data['users'].append(user_id)
        data_store.save_data()
    
    welcome_template = data_store.bot_data['bot_settings']['welcome_message']
    welcome_text = format_welcome_message(welcome_template, message.from_user)
    
    await message.reply(welcome_text, reply_markup=create_user_buttons())

async def callback_query_handler(cq: types.CallbackQuery):
    """Handler for user inline button presses."""
    await cq.answer()
    
    if cq.data == "show_date":
        response_text = get_hijri_date_str()
    elif cq.data == "show_time":
        response_text = get_live_time_str()
    elif cq.data == "show_reminder":
        response_text = get_random_reminder()
    else:
        return

    await bot.send_message(
        cq.from_user.id, 
        response_text,
        protect_content=data_store.bot_data['bot_settings'].get('content_protection', False)
    )

async def message_handler(message: types.Message):
    """Handler for all other user messages."""
    user_id = message.from_user.id
    settings = data_store.bot_data['bot_settings']

    # Maintenance Mode Check
    if settings.get('maintenance_mode', False) and user_id != from_config.ADMIN_CHAT_ID:
        await message.reply(settings.get('maintenance_message', "البوت في الصيانة."))
        return

    # Ban Check
    if user_id in data_store.bot_data['banned_users']:
        return

    # Slow Mode Check
    slow_mode_seconds = settings.get('slow_mode_seconds', 0)
    if slow_mode_seconds > 0:
        last_msg_time = data_store.user_last_message_time.get(user_id)
        if last_msg_time and (datetime.datetime.now() - last_msg_time).total_seconds() < slow_mode_seconds:
            await message.reply(f"⏳ الرجاء الانتظار {slow_mode_seconds} ثواني بين الرسائل.")
            return
        data_store.user_last_message_time[user_id] = datetime.datetime.now()
    
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
    await forward_to_admin(message, bot)
    await message.reply(
        settings.get('reply_message', "تم استلام رسالتك."), 
        reply_markup=create_user_buttons()
    )

def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(start_cmd, commands=['start'])
    dp.register_callback_query_handler(callback_query_handler)
    dp.register_message_handler(message_handler, content_types=types.ContentTypes.ANY)
