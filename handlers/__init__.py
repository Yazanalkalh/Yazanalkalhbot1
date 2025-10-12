from aiogram import Dispatcher

from .admins import register_admin_handlers
from .users import register_user_handlers

def register_all_handlers(dp: Dispatcher):
    # المهم: تسجيل معالجات المشرفين أولاً
    register_admin_handlers(dp)
    
    # ثم تسجيل معالجات المستخدمين
    register_user_handlers(dp)
