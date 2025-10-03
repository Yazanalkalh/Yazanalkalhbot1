from aiogram import Dispatcher
from .admins import register_admin_handlers
from .users import register_user_handlers

def register_all_handlers(dp: Dispatcher):
    # Important: Register admin handlers first
    register_admin_handlers(dp)
    register_user_handlers(dp)
