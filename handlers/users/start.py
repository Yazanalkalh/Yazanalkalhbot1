from aiogram import types, Dispatcher
import data_store
from utils.helpers import format_welcome_message
from keyboards.inline.user_keyboards import create_user_buttons

async def start_cmd(message: types.Message):
    """Handler for the /start command."""
    user_id = message.from_user.id
    if user_id not in data_store.bot_data.get('users', []):
        data_store.bot_data.setdefault('users', []).append(user_id)
        data_store.save_data()
    
    welcome_template = data_store.bot_data.get('bot_settings', {}).get('welcome_message', "أهلاً بك!")
    welcome_text = format_welcome_message(welcome_template, message.from_user)
    
    await message.reply(welcome_text, reply_markup=create_user_buttons())

def register_start_handlers(dp: Dispatcher):
    dp.register_message_handler(start_cmd, commands=['start'])
