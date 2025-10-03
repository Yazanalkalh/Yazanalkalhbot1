from aiogram import types, Dispatcher
import data_store
from utils.helpers import format_welcome_message
from keyboards.inline.user_keyboards import create_user_buttons
from config import ADMIN_CHAT_ID

async def start_cmd(message: types.Message):
    """Handler for the /start command."""
    user_id = message.from_user.id
    
    # Add user to the database if not already present
    if user_id not in data_store.bot_data.get('users', []):
        data_store.bot_data.setdefault('users', []).append(user_id)
        data_store.save_data()
    
    # Format and send the welcome message
    welcome_template = data_store.bot_data.get('bot_settings', {}).get('welcome_message', "👋 أهلًا وسهلًا بك!")
    welcome_text = format_welcome_message(welcome_template, message.from_user)
    
    await message.reply(welcome_text, reply_markup=create_user_buttons())

# --- THIS IS THE MISSING PIECE ---
def register_start_handler(dp: Dispatcher):
    """Registers the handler for the /start command."""
    # We add a filter to ignore the admin, so the admin doesn't get the user welcome message.
    dp.register_message_handler(start_cmd, lambda msg: msg.from_user.id != ADMIN_CHAT_ID, commands=['start'], state="*")
