from aiogram import Dispatcher
from .start import register_start_handlers
from .message_handler import register_user_message_handler
from .callback_handler import register_user_callback_handler

def register_user_handlers(dp: Dispatcher):
    # Handlers with specific commands/filters first
    register_start_handlers(dp)
    register_user_callback_handler(dp)
    # The general message handler last, to catch everything else
    register_user_message_handler(dp)
