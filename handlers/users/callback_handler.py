from aiogram import types, Dispatcher
from loader import bot
import data_store
from utils.helpers import get_hijri_date_str, get_live_time_str, get_random_reminder

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
        protect_content=data_store.bot_data.get('bot_settings', {}).get('content_protection', False)
    )

def register_callback_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(callback_query_handler)
