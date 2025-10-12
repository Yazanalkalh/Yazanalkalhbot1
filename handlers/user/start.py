from aiogram import types, Dispatcher
import data_store
from utils.helpers import format_welcome_message
from keyboards.inline.user_keyboards import create_user_buttons
from config import ADMIN_CHAT_ID

# This file now also includes a "guard" to prevent non-admins from using the /admin command.

async def start_cmd(message: types.Message):
    """Handler for the /start command for regular users."""
    user_id = message.from_user.id
    
    # Add user to the database if not already present
    if user_id not in data_store.bot_data.get('users', []):
        data_store.bot_data.setdefault('users', []).append(user_id)
        data_store.save_data()
    
    # Format and send the welcome message
    welcome_template = data_store.bot_data.get('bot_settings', {}).get('welcome_message', "👋 أهلًا وسهلًا بك!")
    welcome_text = format_welcome_message(welcome_template, message.from_user)
    
    await message.reply(welcome_text, reply_markup=create_user_buttons())

# --- NEW: The "Security Guard" function ---
async def admin_cmd_for_users(message: types.Message):
    """
    This handler catches the /admin command from non-admin users 
    and sends them a warning message.
    """
    warning_text = (
        "⚠️ <b>تنبيه خاص</b> 👑\n\n"
        "هذا الأمر مخصص للمدير فقط 🔒\n"
        "لا يمكنك استخدامه لضمان سلامة عمل البوت.\n\n"
        "<i>استخدم الأزرار المتاحة لك ✨</i>"
    )
    await message.reply(warning_text)

def register_start_handler(dp: Dispatcher):
    """Registers the handlers for /start and the /admin guard."""
    
    # 1. Register the "Security Guard" first. It has priority for the /admin command for non-admins.
    dp.register_message_handler(admin_cmd_for_users, lambda msg: msg.from_user.id != ADMIN_CHAT_ID, commands=['admin'], state="*")
    
    # 2. Register the regular /start handler second. It will only handle /start from non-admins.
    dp.register_message_handler(start_cmd, lambda msg: msg.from_user.id != ADMIN_CHAT_ID, commands=['start'], state="*")
