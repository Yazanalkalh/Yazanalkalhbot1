import datetime
from aiogram import types, Dispatcher
from loader import bot
import data_store
from keyboards.inline import create_user_buttons
from utils.helpers import get_hijri_date_string, get_live_time_string, process_klisha

async def start_cmd(m: types.Message):
    """Handler for the /start command."""
    user_id = m.from_user.id
    if user_id not in data_store.bot_data['users']:
        data_store.bot_data['users'].append(user_id)
        data_store.save_data()
    
    cfg = data_store.bot_data['bot_settings']
    welcome_text = process_klisha(cfg.get('welcome_message'), m.from_user)
    await m.answer(welcome_text, reply_markup=create_user_buttons())

async def user_message_handler(m: types.Message):
    """Handles all incoming messages from non-admin users."""
    user_id = m.from_user.id
    cfg = data_store.bot_data['bot_settings']

    # Maintenance Mode Check
    if cfg.get('maintenance_mode', False):
        await m.answer(cfg.get('maintenance_message', "البوت في الصيانة."))
        return

    # Ban Check
    if user_id in data_store.bot_data.get('banned_users', []):
        return

    # Slow Mode Check
    slow_mode_seconds = cfg.get('slow_mode_seconds', 0)
    if slow_mode_seconds > 0:
        last_msg_time = data_store.user_last_message_time.get(user_id)
        if last_msg_time:
            elapsed = (datetime.datetime.now() - last_msg_time).total_seconds()
            if elapsed < slow_mode_seconds:
                return # Silently ignore
        data_store.user_last_message_time[user_id] = datetime.datetime.now()

    # Dynamic Reply Check
    if m.text and m.text in data_store.bot_data.get('dynamic_replies', {}):
        reply_text = data_store.bot_data['dynamic_replies'][m.text]
        await m.answer(reply_text, reply_markup=create_user_buttons(), protect_content=cfg.get('content_protection', False))
        return

    # Media Type Check
    allowed_types = cfg.get('allowed_media_types', ['text'])
    if m.content_type not in allowed_types:
        await m.answer(cfg.get('media_reject_message'), reply_markup=create_user_buttons())
        return

    # Forward to Admin
    try:
        fw_msg = await m.forward(data_store.config.ADMIN_CHAT_ID)
        data_store.forwarded_message_links[fw_msg.message_id] = {
            "user_id": user_id,
            "original_message_id": m.message_id
        }
    except Exception as e:
        print(f"Could not forward message to admin: {e}")

    # Reply to User
    await m.answer(cfg.get('reply_message'), reply_markup=create_user_buttons(), protect_content=cfg.get('content_protection', False))


async def user_callbacks_handler(cq: types.CallbackQuery):
    """Handles callback queries from user keyboards."""
    await cq.answer()
    cfg_ui = data_store.bot_data['ui_config']
    cfg_bot = data_store.bot_data['bot_settings']
    
    response_text = ""
    if cq.data == "get_date":
        response_text = get_hijri_date_string()
    elif cq.data == "get_time":
        response_text = get_live_time_string(cfg_ui.get('timezone', 'Asia/Aden'))
    elif cq.data == "get_reminder":
        reminders = data_store.bot_data.get('reminders', [])
        response_text = random.choice(reminders) if reminders else "لا توجد تذكيرات حالياً."
        
    if response_text:
        await cq.message.answer(response_text, protect_content=cfg_bot.get('content_protection', False))

def register_user_handlers(dp: Dispatcher):
    """Registers all handlers for regular users."""
    dp.register_message_handler(start_cmd, commands=['start'], state="*")
    dp.register_message_handler(user_message_handler, content_types=types.ContentTypes.ANY, state="*")
    dp.register_callback_query_handler(user_callbacks_handler, state="*")
