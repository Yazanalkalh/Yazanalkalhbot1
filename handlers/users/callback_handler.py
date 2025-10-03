from aiogram import types, Dispatcher
from loader import bot
import data_store
from utils.helpers import get_hijri_date_str, get_live_time_str, get_random_reminder
from .message_handler import is_regular_user

async def callback_query_handler(cq: types.CallbackQuery):
    """Handler for user inline button presses."""
    await cq.answer()
    
    response_text = ""
    if cq.data == "show_date":
        response_text = get_hijri_date_str()
    elif cq.data == "show_time":
        response_text = get_live_time_str()
    elif cq.data == "show_reminder":
        response_text = get_random_reminder()
    else:
        return

    if response_text:
        await bot.send_message(
            cq.from_user.id, 
            response_text,
            protect_content=data_store.bot_data['bot_settings'].get('content_protection', False)
        )

# --- THIS IS THE MISSING PIECE THAT FIXES THE ERROR ---
def register_callback_handler(dp: Dispatcher):
    """Registers the callback query handler for regular users."""
    # We add the is_regular_user filter to ensure admins don't accidentally trigger this
    dp.register_callback_query_handler(callback_query_handler, is_regular_user)
