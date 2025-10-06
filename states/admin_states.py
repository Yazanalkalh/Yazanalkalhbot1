from aiogram.dispatcher.filters.state import State, StatesGroup

# This is the final, definitive list of all possible states for BOTH control panels.

class AdminStates(StatesGroup):
    # /admin panel states
    waiting_for_dyn_reply_keyword = State()
    waiting_for_dyn_reply_content = State()
    waiting_for_dyn_reply_delete = State()
    waiting_for_dyn_replies_file = State()
    waiting_for_new_reminder = State()
    waiting_for_delete_reminder = State()
    waiting_for_reminders_file = State()
    waiting_for_ban_id = State()
    waiting_for_unban_id = State()
    waiting_for_new_channel_msg = State()
    waiting_for_delete_channel_msg = State()
    waiting_for_instant_channel_post = State()
    waiting_for_scheduled_post_content = State()
    waiting_for_scheduled_post_datetime = State()
    waiting_for_broadcast_message = State()
    waiting_for_date_button_label = State()
    waiting_for_time_button_label = State()
    waiting_for_reminder_button_label = State()
    waiting_for_timezone = State()
    waiting_for_welcome_message = State()
    waiting_for_reply_message = State()
    waiting_for_channel_id = State()
    waiting_for_schedule_interval = State()
    waiting_for_add_media_type = State()
    waiting_for_remove_media_type = State()
    waiting_for_media_reject_message = State()
    waiting_for_spam_limit = State()
    waiting_for_spam_window = State()
    waiting_for_slow_mode = State()
    waiting_for_clear_user_id = State()

    # /hijri (Advanced) panel states
    waiting_for_force_channel_id = State()
    waiting_for_new_text = State() # For the text manager
