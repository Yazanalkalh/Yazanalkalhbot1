from aiogram import Dispatcher

from .panel import register_panel_handlers
from .fsm_handlers import register_fsm_handlers
# --- NEW: Import BOTH new handlers ---
from .advanced_panel import register_advanced_panel_handler
from .chat_admin_handler import register_chat_admin_handler


def register_admin_handlers(dp: Dispatcher):
    """
    This function acts as the "General HR Manager" for the admin section.
    It now registers ALL admin-related handlers, including the new advanced ones.
    """
    # Register the original handlers
    register_panel_handlers(dp)
    register_fsm_handlers(dp)
    
    # --- NEW: Register BOTH new employees ---
    register_advanced_panel_handler(dp)
    register_chat_admin_handler(dp)
