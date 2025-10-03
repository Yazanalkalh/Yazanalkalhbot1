from aiogram import Dispatcher

from .start import register_start_handlers
from .callback_handler import register_callback_handlers
from .message_handler import register_message_handlers

def register_user_handlers(dp: Dispatcher):
    register_start_handlers(dp)
    register_callback_handlers(dp)
    register_message_handlers(dp)
