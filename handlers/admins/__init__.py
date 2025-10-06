from aiogram import Dispatcher

from .panel import register_panel_handlers
from .fsm_handlers import register_fsm_handlers
# NEW: Import BOTH new handlers
from .advanced_panel import register_advanced_panel_handler
from .chat_admin_handler import register_chat_admin_handler


def register_admin_handlers(dp: Dispatcher):
    """
    This function acts as the "General HR Manager" for the admin section.
    It now registers handlers in the correct order: MORE SPECIFIC handlers first.
    """
    
    # 1. Register the specialist handlers for the advanced panel and new chats first.
    #    These have specific triggers (adv_ prefix, new chat member).
    register_advanced_panel_handler(dp)
    register_chat_admin_handler(dp)
    
    # 2. Register the more general handlers for the old panel and FSM last.
    #    These act as a "catch-all" for other admin actions.
    register_panel_handlers(dp)
    register_fsm_handlers(dp)
