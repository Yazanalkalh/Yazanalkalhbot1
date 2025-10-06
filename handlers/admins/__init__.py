from aiogram import Dispatcher
from .panel import register_panel_handlers
# --- NEW: Import the new advanced panel handler ---
from .advanced_panel import register_advanced_panel_handler
from .fsm_handlers import register_fsm_handlers

def register_admin_handlers(dp: Dispatcher):
    """
    This function acts as an "HR Manager" for the admin section.
    It now registers the new advanced panel alongside the old ones.
    """
    register_panel_handlers(dp)
    register_fsm_handlers(dp)
    # --- NEW: Tell the HR Manager to register the new employee ---
    register_advanced_panel_handler(dp)
