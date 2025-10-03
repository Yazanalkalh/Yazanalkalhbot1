from aiogram.dispatcher.filters.state import State, StatesGroup

class AdminStates(StatesGroup):
    # Dynamic Replies
    waiting_for_dyn_reply_keyword = State()
    waiting_for_dyn_reply_content = State()
    waiting_for_dyn_reply_delete = State()
    
    # Reminders
    waiting_for_new_reminder = State()
    waiting_for_delete_reminder = State()
    
    # Ban Management
    waiting_for_ban_id = State()
    waiting_for_unban_id = State()
    
    # Channel Messages
    waiting_for_new_channel_msg = State()
    waiting_for_delete_channel_msg = State()
    waiting_for_instant_channel_post = State()
    waiting_for_scheduled_post_text = State()
    waiting_for_scheduled_post_datetime = State()

    # Broadcast
    waiting_for_broadcast_message = State()

    # UI Customization
    waiting_for_date_button_label = State()
    waiting_for_time_button_label = State()
    waiting_for_reminder_button_label = State()
    waiting_for_timezone = State()
    waiting_for_welcome_message = State()
    waiting_for_reply_message = State()

    # Channel Settings
    waiting_for_channel_id = State()
    waiting_for_schedule_interval = State()
    
    # Media Settings
    waiting_for_add_media_type = State()
    waiting_for_remove_media_type = State()
    waiting_for_media_reject_message = State()
