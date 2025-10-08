from aiogram import Dispatcher

# Import all handler registration functions
from .panel import register_panel_handlers
from .fsm_handlers import register_fsm_handlers
from .advanced_panel import register_advanced_panel_handler
from .chat_admin_handler import register_chat_admin_handler
from .text_manager_handler import register_text_manager_handler

def register_admin_handlers(dp: Dispatcher):
    """
    Registers ALL admin handlers in the correct order: specialists first.
    This order is critical to prevent conflicts.
    """
    # 1. Register specialist handlers first. They have specific triggers.
    register_advanced_panel_handler(dp)
    register_chat_admin_handler(dp)
    register_text_manager_handler(dp)
    
    # 2. Register the more general handlers last.
    register_panel_handlers(dp)
    register_fsm_handlers(dp)
