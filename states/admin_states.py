from aiogram.dispatcher.filters.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_for_new_reminder = State()
    waiting_for_ban_id = State()
    waiting_for_unban_id = State()
    waiting_for_broadcast_message = State()
    confirm_broadcast = State()
