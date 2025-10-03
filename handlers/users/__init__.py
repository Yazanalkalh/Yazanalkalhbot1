from aiogram import Dispatcher

from .start import register_start_handlers
from .callback_handler import register_callback_handlers
from .message_handler import register_message_handler # <-- Corrected from plural to singular

def register_user_handlers(dp: Dispatcher):
    """Registers all user-side handlers."""
    register_start_handlers(dp)
    register_callback_handlers(dp)
    register_message_handler(dp) # <-- Corrected from plural to singular
