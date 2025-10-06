from aiogram import types, Dispatcher
from config import ADMIN_CHAT_ID
from loader import bot
from utils.database import add_pending_channel

# This is the VIP upgraded "Border Guard". It uses the 'my_chat_member'
# handler to detect joining BOTH groups and channels reliably.

async def on_bot_status_change(update: types.ChatMemberUpdated):
    """
    This powerful handler triggers on any status change for the bot in any chat.
    e.g., being added to a group, promoted in a channel, or even being kicked.
    """
    # We are interested in the moment the bot becomes a member or an admin
    if update.new_chat_member.status in ["member", "administrator"]:
        chat_id = update.chat.id
        chat_title = update.chat.title

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
        try:
            await bot.send_message(ADMIN_CHAT_ID, text)
        except Exception as e:
            print(f"Failed to notify admin about new chat: {e}")

def register_chat_admin_handler(dp: Dispatcher):
    """Registers the handler for the bot's chat membership changes."""
    # We register our new powerful handler to listen for 'my_chat_member' updates.
    # This is the correct, modern way to track where the bot is.
    dp.register_my_chat_member_handler(on_bot_status_change)
