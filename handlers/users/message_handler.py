from aiogram import types, Dispatcher
from utils import database, texts
from utils.helpers import forward_to_admin

async def user_message_handler(message: types.Message):
    """Handler for all other user messages."""
    user_id = message.from_user.id
    
    # 1. Check if user is banned
    if database.is_user_banned(user_id):
        return # Silently ignore banned users

    # 2. Check for maintenance mode
    if database.get_setting('maintenance_mode', False) and user_id != database.ADMIN_CHAT_ID:
        await message.reply(texts.get_text("user_maintenance_mode"))
        return
        
    # 3. If everything is OK, forward to admin and send a confirmation reply
    await forward_to_admin(message)
    await message.reply(texts.get_text("user_default_reply"))

def register_user_message_handler(dp: Dispatcher):
    # This handler catches any message in a private chat that isn't a command
    dp.register_message_handler(
        user_message_handler, 
        lambda message: message.chat.type == types.ChatType.PRIVATE,
        content_types=types.ContentTypes.ANY,
        state=None
    )
