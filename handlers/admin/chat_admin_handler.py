from aiogram import types, Dispatcher
from config import ADMIN_CHAT_ID
from loader import bot
# NEW: We need the database function to add the request
from utils.database import add_pending_channel

# This is a new, isolated file. Its only job is to detect when the bot
# is added to a new channel or group and notify the admin.

async def on_bot_join_chat(message: types.Message):
    """
    This handler triggers when the bot is added to a new group or channel.
    It adds the chat to the pending list and notifies the admin.
    """
    # This check ensures the event is about the bot itself joining
    for member in message.new_chat_members:
        if member.id == bot.id:
            chat_id = message.chat.id
            chat_title = message.chat.title
            
            # Add to the database for admin approval
            add_pending_channel(chat_id, chat_title)
            
            # Notify the admin
            text = (
                f"⏳ **طلب انضمام جديد**\n\n"
                f"تمت إضافة البوت إلى قناة/مجموعة جديدة وهي تنتظر موافقتك:\n\n"
                f"**الاسم:** {chat_title}\n"
                f"**ID:** `{chat_id}`\n\n"
                f"اذهب إلى **لوحة التحكم المتقدمة (`/hijri`)** -> **إدارة القنوات** للموافقة أو الرفض."
            )
            await bot.send_message(ADMIN_CHAT_ID, text)
            break # No need to check other new members

def register_chat_admin_handler(dp: Dispatcher):
    """Registers the handler for chat membership changes."""
    # This handler specifically looks for messages of type "new chat members"
    dp.register_message_handler(
        on_bot_join_chat,
        content_types=types.ContentTypes.NEW_CHAT_MEMBERS
    )
