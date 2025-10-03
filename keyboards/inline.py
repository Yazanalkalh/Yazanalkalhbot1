from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import data_store

def create_user_buttons():
    """Creates the main keyboard for regular users."""
    cfg = data_store.bot_data['ui_config']
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text=cfg.get('date_button_label', '📅 التاريخ'), callback_data="get_date"),
        InlineKeyboardButton(text=cfg.get('time_button_label', '⏰ الساعة الان'), callback_data="get_time"),
        InlineKeyboardButton(text=cfg.get('reminder_button_label', '💡 تذكير يومي'), callback_data="get_reminder")
    )
    return keyboard

def create_admin_panel():
    """Creates the main admin control panel keyboard."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📝 الردود الديناميكية", callback_data="admin_dyn_replies"),
        InlineKeyboardButton("💭 إدارة التذكيرات", callback_data="admin_reminders"),
        InlineKeyboardButton("📢 منشورات القناة", callback_data="admin_channel"),
        InlineKeyboardButton("🚫 إدارة الحظر", callback_data="admin_ban"),
        InlineKeyboardButton("📤 النشر للجميع", callback_data="admin_broadcast"),
        InlineKeyboardButton("🎨 تخصيص الواجهة", callback_data="admin_customize_ui"),
        InlineKeyboardButton("🛡️ الحماية والأمان", callback_data="admin_security"),
        InlineKeyboardButton("🧠 إدارة الذاكرة", callback_data="admin_memory_management"),
        InlineKeyboardButton("📊 عرض الإحصائيات", callback_data="admin_stats"),
        InlineKeyboardButton("🚀 حالة النشر", callback_data="deploy_status"),
        InlineKeyboardButton("❌ إغلاق", callback_data="close_panel")
    )
    return keyboard

def get_menu_keyboard(menu_type: str):
    """Generates sub-menu keyboards for the admin panel."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    cfg = data_store.bot_data['bot_settings']
    
    buttons = []
    if menu_type == "admin_dyn_replies":
        buttons = [("➕ برمجة رد جديد", "add_dyn_reply"), ("🗑️ حذف رد", "delete_dyn_reply"), ("📋 عرض الردود", "show_dyn_replies")]
    elif menu_type == "admin_reminders":
        buttons = [("➕ إضافة تذكير", "add_reminder"), ("🗑️ حذف تذكير", "delete_reminder"), ("📋 عرض التذكيرات", "show_reminders")]
    elif menu_type == "admin_channel":
        buttons = [("➕ إضافة رسالة تلقائية", "add_channel_msg"), ("🗑️ حذف رسالة تلقائية", "delete_channel_msg"), ("📋 عرض الرسائل", "show_channel_msgs"), ("📤 نشر فوري", "instant_channel_post"), ("⏰ جدولة منشور", "schedule_post"), ("⚙️ إعدادات القناة", "admin_channel_settings")]
    elif menu_type == "admin_ban":
        buttons = [("🚫 حظر مستخدم", "ban_user"), ("✅ إلغاء الحظر", "unban_user"), ("📋 عرض المحظورين", "show_banned")]
    elif menu_type == "admin_broadcast":
        buttons = [("📤 إرسال رسالة الآن", "send_broadcast")]
    elif menu_type == "admin_customize_ui":
        buttons = [("✏️ تعديل زر التاريخ", "edit_date_button"), ("✏️ تعديل زر الساعة", "edit_time_button"), ("✏️ تعديل زر التذكير", "edit_reminder_button"), ("🌍 تعديل المنطقة الزمنية", "set_timezone"), ("👋 تعديل رسالة الترحيب", "edit_welcome_msg"), ("💬 تعديل رسالة الرد", "edit_reply_msg")]
    elif menu_type == "admin_security":
        maintenance_text = "✅ إيقاف الصيانة" if cfg.get('maintenance_mode') else "⛔ تفعيل الصيانة"
        protection_text = "🔓 إلغاء حماية المحتوى" if cfg.get('content_protection') else "🔒 تفعيل حماية المحتوى"
        buttons = [(maintenance_text, "toggle_maintenance"), (protection_text, "toggle_protection"), ("🖼️ إدارة الوسائط", "media_settings"), ("🔧 منع التكرار", "spam_settings"), ("⏳ وضع التباطؤ", "slow_mode_settings")]
    elif menu_type == "admin_memory_management":
        buttons = [("🗑️ مسح بيانات مستخدم", "clear_user_data"), ("🧹 مسح ذاكرة التباطؤ", "clear_spam_cache")]
    elif menu_type == "admin_channel_settings":
        buttons = [("🆔 تعديل ID القناة", "set_channel_id"), ("🕰️ تعديل فترة النشر التلقائي", "set_schedule_interval")]
    elif menu_type == "media_settings":
        buttons = [("➕ السماح بنوع", "add_media_type"), ("➖ منع نوع", "remove_media_type"), ("✍️ تعديل رسالة الرفض", "edit_media_reject_message")]
    elif menu_type == "spam_settings":
        buttons = [("🔢 تعديل حد الرسائل", "set_spam_limit"), ("⏱️ تعديل الفترة الزمنية", "set_spam_window")]
    elif menu_type == "slow_mode_settings":
        buttons = [("⏳ تعديل فترة التباطؤ", "set_slow_mode")]
        
    for text, cb_data in buttons:
        keyboard.add(InlineKeyboardButton(text, callback_data=cb_data))
        
    if menu_type not in ["admin_panel"]:
        keyboard.add(InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="back_to_main"))
        
    return keyboard

def back_kb(back_to: str = "back_to_main"):
    """Creates a simple back keyboard."""
    return InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة", callback_data=back_to))

def add_another_kb(add_cb: str, back_cb: str):
    """Creates a keyboard with 'Add Another' and 'Back' options."""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ إضافة المزيد", callback_data=add_cb),
        InlineKeyboardButton("🔙 العودة", callback_data=back_cb)
    )
    return kb 
