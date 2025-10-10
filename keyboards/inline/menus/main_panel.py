from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_admin_panel() -> InlineKeyboardMarkup:
    """Creates the main admin control panel keyboard."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📝 الردود التلقائية ", callback_data="admin_dyn_replies"),
        InlineKeyboardButton("💭 إدارة التذكيرات", callback_data="admin_reminders"),
        InlineKeyboardButton("📢 منشورات القناة", callback_data="admin_channel"),
        InlineKeyboardButton("🚫 إدارة الحظر", callback_data="admin_ban"),
        InlineKeyboardButton("📤 النشر للجميع", callback_data="admin_broadcast"),
        InlineKeyboardButton("🎨 تخصيص الواجهة", callback_data="admin_customize_ui"),
        InlineKeyboardButton("🛡️ الحماية والأمان", callback_data="admin_security"),
        InlineKeyboardButton("🧠 إدارة الذاكرة", callback_data="admin_memory_management"),
        InlineKeyboardButton("⚙️ إعدادات القناة", callback_data="admin_channel_settings"),
        InlineKeyboardButton("📊 عرض الإحصائيات", callback_data="admin_stats"),
        InlineKeyboardButton("🚀 حالة النشر", callback_data="deploy_status"),
        InlineKeyboardButton("❌ إغلاق", callback_data="close_panel")
    )
    return keyboard
