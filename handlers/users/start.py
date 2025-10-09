from aiogram import types, Dispatcher
from utils import database, texts
from keyboards.inline.user_keyboards import create_user_buttons
from config import ADMIN_CHAT_ID

async def start_cmd(message: types.Message):
    """Handler for the /start command."""
    user = message.from_user
    # Add user to the database
    database.add_user(user.id, user.full_name, user.username)
    
    # Format and send the welcome message
    welcome_text = texts.get_text("user_welcome", name=user.first_name)
    await message.reply(welcome_text, reply_markup=create_user_buttons())

# A "guard" to prevent non-admins from accessing admin commands
async def admin_cmd_guard(message: types.Message):
    await message.reply("⚠️ هذا الأمر مخصص للمدير فقط.")

def register_start_handlers(dp: Dispatcher):
    # The guard has a filter to catch anyone who is NOT the admin trying /admin
    dp.register_message_handler(admin_cmd_guard, lambda msg: msg.from_user.id != ADMIN_CHAT_ID, commands=['admin', 'hijri', 'yazan'], state="*")
    # The regular /start handler
    dp.register_message_handler(start_cmd, commands=['start'], state="*")
