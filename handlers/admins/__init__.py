import sys
from aiogram import Dispatcher

# Import all handler registration functions
from .panel import register_panel_handlers
from .fsm_handlers import register_fsm_handlers
from .advanced_panel import register_advanced_panel_handler
from .chat_admin_handler import register_chat_admin_handler
from .text_manager_handler import register_text_manager_handler

def register_admin_handlers(dp: Dispatcher):
    """
    Registers ALL admin handlers in the correct order:
    
    1. Main Panel Handlers (General Commands & Callbacks - must be first)
    2. Specialist Handlers (Advanced, Chat, Text) - these must have explicit filters.
    3. FSM Handlers (State-based logic - must be last)
    """
    
    # 1. المعالج العام (يجب أن يسجل أولاً لاحتوائه على أمر /admin والمعالج العام للأزرار)
    register_panel_handlers(dp) 
    
    # 2. المعالجات المتخصصة (تحتاج لفلاتر قوية لتجنب اعتراض الرسائل)
    register_advanced_panel_handler(dp)
    register_chat_admin_handler(dp)
    register_text_manager_handler(dp)
    
    # 3. معالجات الحالات FSM (يجب أن تسجل في النهاية)
    register_fsm_handlers(dp)

    print("✅ Admin Handlers Registered in correct priority order.")
