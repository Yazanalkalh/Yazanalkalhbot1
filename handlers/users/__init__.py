from aiogram import Dispatcher
from .start import register_start_handlers
from .callback_handler import register_callback_handler
from .message_handler import register_message_handler

def register_user_handlers(dp: Dispatcher):
    """Registers all handlers for regular users."""
    register_start_handlers(dp)
    register_callback_handler(dp)
    register_message_handler(dp)
