from aiogram import Dispatcher
from .admins import register_admin_handlers
from .users import register_user_handlers

def register_all_handlers(dp: Dispatcher):
    # Admin handlers are registered first to have priority
    register_admin_handlers(dp)
    # User handlers are registered second
    register_user_handlers(dp)
