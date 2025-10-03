from aiogram import types, Dispatcher
from loader import bot
import data_store
from utils.helpers import get_hijri_date_str, get_live_time_str, get_random_reminder

# We don't need a special filter here, this should work for any non-banned user.

async def callback_query_handler(cq: types.CallbackQuery):
    """Handler for user inline button presses."""
    # Ban Check
    if cq.from_user.id in data_store.bot_data['banned_users']:
        await cq.answer("🚫 أنت محظور من استخدام البوت.", show_alert=True)
        return

    await cq.answer()
    
    response_text = ""
    if cq.data == "show_date":
        response_text = get_hijri_date_str()
    elif cq.data == "show_time":
        response_text = get_live_time_str()
    elif cq.data == "show_reminder":
        response_text = get_random_reminder()
    
    if response_text:
        try:
            await bot.send_message(
                chat_id=cq.from_user.id, 
                text=response_text,
                protect_content=data_store.bot_data['bot_settings'].get('content_protection', False)
            )
        except Exception as e:
            print(f"Error sending callback response: {e}")

def register_callback_handler(dp: Dispatcher):
    """Registers the callback query handler for regular users."""
    dp.register_callback_query_handler(callback_query_handler, state=None)
