from aiogram import Dispatcher

from .panel import register_panel_handlers
from .fsm_handlers import register_fsm_handlers
from .advanced_panel import register_advanced_panel_handler
from .chat_admin_handler import register_chat_admin_handler
# --- NEW: Import the final new handler ---
from .text_manager_handler import register_text_manager_handler


def register_admin_handlers(dp: Dispatcher):
    """
    This function acts as the "General HR Manager" for the admin section.
    It now registers ALL handlers in the correct order: specialists first.
    """
    
    # 1. Register all specialist handlers first.
    # These have specific triggers (adv_, tm_, new chat member).
    register_advanced_panel_handler(dp)
    register_chat_admin_handler(dp)
    register_text_manager_handler(dp) # The new employee is now officially registered
    
    # 2. Register the more general handlers last.
    # These act as a "catch-all" for other admin actions.
    register_panel_handlers(dp)
    register_fsm_handlers(dp)
