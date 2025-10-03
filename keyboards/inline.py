from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import data_store

def create_user_buttons() -> InlineKeyboardMarkup:
    """Creates the main keyboard for regular users."""
    cfg = data_store.bot_data['ui_config']
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text=cfg['date_button_label'], callback_data="show_date"),
        InlineKeyboardButton(text=cfg['time_button_label'], callback_data="show_time"),
        InlineKeyboardButton(text=cfg['reminder_button_label'], callback_data="show_reminder")
    )
    return keyboard

def create_admin_panel() -> InlineKeyboardMarkup:
    """Creates the main admin control panel keyboard."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📝 الردود الديناميكية", "admin_dyn_replies"),
        InlineKeyboardButton("💭 إدارة التذكيرات", "admin_reminders"),
        InlineKeyboardButton("📢 منشورات القناة", "admin_channel"),
        InlineKeyboardButton("🚫 إدارة الحظر", "admin_ban"),
        InlineKeyboardButton("📤 النشر للجميع", "admin_broadcast"),
        InlineKeyboardButton("🎨 تخصيص الواجهة", "admin_customize_ui"),
        InlineKeyboardButton("🛡️ الحماية والأمان", "admin_security"),
        InlineKeyboardButton("🧠 إدارة الذاكرة", "admin_memory_management"),
        InlineKeyboardButton("⚙️ إعدادات القناة", "admin_channel_settings"),
        InlineKeyboardButton("📊 عرض الإحصائيات", "admin_stats"),
        InlineKeyboardButton("🚀 حالة النشر", "deploy_status"),
        InlineKeyboardButton("❌ إغلاق", "close_panel")
    )
    return keyboard

def get_menu_keyboard(menu_type: str) -> InlineKeyboardMarkup:
    """Generates specific sub-menus for the admin panel."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    cfg = data_store.bot_data['bot_settings']
    
    buttons_map = {
        "admin_dyn_replies": [("➕ برمجة رد جديد", "add_dyn_reply"), ("📝 عرض الردود", "show_dyn_replies"), ("🗑️ حذف رد", "delete_dyn_reply")],
        "admin_reminders": [("➕ إضافة تذكير", "add_reminder"), ("📝 عرض التذكيرات", "show_reminders"), ("🗑️ حذف تذكير", "delete_reminder")],
        "admin_channel": [("➕ إضافة رسالة تلقائية", "add_channel_msg"), ("📝 عرض الرسائل", "show_channel_msgs"), ("🗑️ حذف رسالة", "delete_channel_msg"), ("📤 نشر فوري", "instant_channel_post"), ("⏰ جدولة منشور", "schedule_post")],
        "admin_ban": [("🚫 حظر مستخدم", "ban_user"), ("✅ إلغاء حظر", "unban_user"), ("📋 قائمة المحظورين", "show_banned")],
        "admin_broadcast": [("📤 إرسال رسالة جماعية", "send_broadcast")],
        "admin_channel_settings": [("🆔 تعديل ID القناة", "set_channel_id"), ("⏰ تعديل فترة النشر التلقائي", "set_schedule_interval")],
        "admin_customize_ui": [
            ("✏️ تعديل زر التاريخ", "edit_date_button"), ("✏️ تعديل زر الساعة", "edit_time_button"),
            ("✏️ تعديل زر التذكير", "edit_reminder_button"), ("🌍 تعديل المنطقة الزمنية", "set_timezone"),
            ("👋 تعديل رسالة الترحيب", "edit_welcome_msg"), ("💬 تعديل رسالة الرد", "edit_reply_msg")
        ],
        "admin_security": [
            ("⚙️ وضع الصيانة" if not cfg.get('maintenance_mode', False) else "▶️ إيقاف الصيانة", "toggle_maintenance"),
            ("🔒 تفعيل الحماية" if not cfg.get('content_protection', False) else "🔓 إلغاء الحماية", "toggle_protection"),
            ("🖼️ إدارة الوسائط", "media_settings"), ("🔧 منع التكرار", "spam_settings"), ("⏳ التباطؤ", "slow_mode_settings")
        ],
        "media_settings": [("➕ إضافة نوع مسموح", "add_media_type"), ("➖ إزالة نوع", "remove_media_type"), ("✍️ تعديل رسالة الرفض", "edit_media_reject_message")],
        "spam_settings": [("🔢 تعديل حد الرسائل", "set_spam_limit"), ("⏱️ تعديل الفترة الزمنية", "set_spam_window")],
        "slow_mode_settings": [("⏳ تعديل فترة التباطؤ", "set_slow_mode")],
        "admin_memory_management": [("🗑️ مسح بيانات مستخدم", "clear_user_data"), ("🧹 مسح ذاكرة التباطؤ", "clear_spam_cache")]
    }
    
    buttons = [InlineKeyboardButton(text, cb) for text, cb in buttons_map.get(menu_type, [])]
    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton("🔙 العودة للوحة التحكم", "back_to_main"))
    return keyboard

def back_kb(callback_data: str = "back_to_main") -> InlineKeyboardMarkup:
    """Creates a simple back button keyboard."""
    return InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة", callback_data))

def add_another_kb(add_callback: str, back_callback: str) -> InlineKeyboardMarkup:
    """Creates an 'Add Another' and 'Back' keyboard."""
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("➕ إضافة المزيد", add_callback),
        InlineKeyboardButton("🔙 العودة", back_callback)
    )
