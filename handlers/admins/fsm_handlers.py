from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
import data_store
from keyboards.inline.admin_keyboards import create_admin_panel, add_another_kb
import pytz
import datetime
import asyncio

# This file contains all the logic for handling messages once the bot is in a "waiting state" (FSM).
# Each function here corresponds to a specific state defined in states/admin_states.py.

def is_admin(message: types.Message):
    """A filter to check if the user is an admin."""
    return message.from_user.id == ADMIN_CHAT_ID

# --- All Handler Functions (Same as previous, omitted for brevity) ---

# --- Handler Registration ---
def register_fsm_handlers(dp: Dispatcher):
    """Registers all the FSM handlers."""
    # Universal cancel command
    dp.register_message_handler(cancel_cmd, is_admin, commands=['cancel'], state='*')
    
    # Dynamic Replies
    dp.register_message_handler(dyn_reply_keyword_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_keyword)
    dp.register_message_handler(dyn_reply_content_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_dyn_reply_content)
    dp.register_message_handler(dyn_reply_delete_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_delete)

    # Reminders
    dp.register_message_handler(add_reminder_handler, is_admin, state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(delete_reminder_handler, is_admin, state=AdminStates.waiting_for_delete_reminder)

    # Ban/Unban
    dp.register_message_handler(ban_user_handler, is_admin, state=AdminStates.waiting_for_ban_id)
    dp.register_message_handler(unban_user_handler, is_admin, state=AdminStates.waiting_for_unban_id)

    # Channel Messages
    dp.register_message_handler(add_channel_msg_handler, is_admin, state=AdminStates.waiting_for_new_channel_msg)
    dp.register_message_handler(delete_channel_msg_handler, is_admin, state=AdminStates.waiting_for_delete_channel_msg)
    dp.register_message_handler(instant_post_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_instant_channel_post)
    dp.register_message_handler(scheduled_post_text_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_scheduled_post_text)
    dp.register_message_handler(scheduled_post_datetime_handler, is_admin, state=AdminStates.waiting_for_scheduled_post_datetime)

    # Broadcast
    dp.register_message_handler(broadcast_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_broadcast_message)

    # UI Customization
    dp.register_message_handler(lambda m,s: simple_ui_text_handler(m, s, 'date_button_label', "✅ تم تحديث اسم الزر."), is_admin, state=AdminStates.waiting_for_date_button_label)
    dp.register_message_handler(lambda m,s: simple_ui_text_handler(m, s, 'time_button_label', "✅ تم تحديث اسم الزر."), is_admin, state=AdminStates.waiting_for_time_button_label)
    dp.register_message_handler(lambda m,s: simple_ui_text_handler(m, s, 'reminder_button_label', "✅ تم تحديث اسم الزر."), is_admin, state=AdminStates.waiting_for_reminder_button_label)
    dp.register_message_handler(set_timezone_handler, is_admin, state=AdminStates.waiting_for_timezone)
    dp.register_message_handler(lambda m,s: simple_settings_text_handler(m, s, 'welcome_message', "✅ تم تحديث رسالة البدء."), is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_welcome_message)
    dp.register_message_handler(lambda m,s: simple_settings_text_handler(m, s, 'reply_message', "✅ تم تحديث رسالة الرد."), is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_reply_message)
    
    # Channel Settings
    dp.register_message_handler(set_channel_id_handler, is_admin, state=AdminStates.waiting_for_channel_id)
    dp.register_message_handler(schedule_interval_handler, is_admin, state=AdminStates.waiting_for_schedule_interval)

    # Media Settings
    dp.register_message_handler(lambda m,s: media_type_handler(m, s, True), is_admin, state=AdminStates.waiting_for_add_media_type)
    dp.register_message_handler(lambda m,s: media_type_handler(m, s, False), is_admin, state=AdminStates.waiting_for_remove_media_type)
    dp.register_message_handler(lambda m,s: simple_settings_text_handler(m, s, 'media_reject_message', "✅ تم تحديث رسالة الرفض."), is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_media_reject_message)
