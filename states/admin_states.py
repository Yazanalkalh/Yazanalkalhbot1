from aiogram.dispatcher.filters.state import State, StatesGroup

# This file defines all the "waiting states" for the admin panel.
# Each state represents a point where the bot is waiting for the admin's input.

class AdminStates(StatesGroup):
    # Dynamic Replies states
    waiting_for_dyn_reply_keyword = State()
    waiting_for_dyn_reply_content = State()
    waiting_for_dyn_reply_delete = State()
    
    # Reminders states
    waiting_for_new_reminder = State()
    waiting_for_delete_reminder = State()
    
    # Ban Management states
    waiting_for_ban_id = State()
    waiting_for_unban_id = State()
    
    # Channel Messages states
    waiting_for_new_channel_msg = State()
    waiting_for_delete_channel_msg = State()
    waiting_for_instant_channel_post = State()
    waiting_for_scheduled_post_text = State()
    waiting_for_scheduled_post_datetime = State()

    # Broadcast state
    waiting_for_broadcast_message = State()

    # --- THIS IS THE UPDATE ---
    # UI Customization states are now fully defined
    waiting_for_date_button_label = State()
    waiting_for_time_button_label = State()
    waiting_for_reminder_button_label = State()
    waiting_for_timezone = State()
    waiting_for_welcome_message = State()
    waiting_for_reply_message = State()
    # --------------------------

    # Channel Settings states
    waiting_for_channel_id = State()
    waiting_for_schedule_interval = State()
    
    # Media Settings states (from Security)
    waiting_for_add_media_type = State()
    waiting_for_remove_media_type = State()
    waiting_for_media_reject_message = State()
