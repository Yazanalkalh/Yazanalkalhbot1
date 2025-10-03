from aiogram import Dispatcher
from .panel import register_panel_handlers
from .fsm_handlers import register_fsm_handlers

def register_admin_handlers(dp: Dispatcher):
    register_panel_handlers(dp)
    register_fsm_handlers(dp)
