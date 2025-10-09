from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_admin_panel() -> InlineKeyboardMarkup:
    """Creates the main admin control panel keyboard."""
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("💭 إدارة التذكيرات", callback_data="menu_reminders"),
        InlineKeyboardButton("🚫 إدارة الحظر", callback_data="menu_ban"),
        InlineKeyboardButton("📤 النشر للجميع", callback_data="broadcast"),
        InlineKeyboardButton("📊 عرض الإحصائيات", callback_data="admin_stats"),
        InlineKeyboardButton("❌ إغلاق", callback_data="close_panel")
    )

def get_reminders_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton("➕ إضافة تذكير", callback_data="add_reminder"),
        InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")
    )

def get_ban_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🚫 حظر مستخدم", callback_data="ban_user"),
        InlineKeyboardButton("✅ إلغاء حظر", callback_data="unban_user"),
        InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")
    )

def get_broadcast_confirmation_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("✅ نعم، أرسل الآن", callback_data="confirm_broadcast"),
        InlineKeyboardButton("❌ إلغاء", callback_data="cancel_broadcast")
    )

def back_to_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
