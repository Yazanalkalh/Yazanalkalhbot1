from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import data_store

def create_admin_panel():
    """ينشئ لوحة التحكم الرئيسية الكاملة للمشرف."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    cfg = data_store.bot_data['bot_settings']
    
    buttons = [
        ("📝 الردود الديناميكية", "admin_dyn_replies"), 
        ("💭 إدارة التذكيرات", "admin_reminders"),
        ("📢 إدارة منشورات القناة", "admin_channel"), 
        ("⚙️ إعدادات القناة", "admin_channel_settings"),
        ("🚫 إدارة الحظر", "admin_ban"),
        ("📤 النشر للجميع", "admin_broadcast"), 
        ("🎨 تخصيص واجهة البوت", "admin_customize_ui"), 
        ("🛡️ إعدادات الحماية والأمان", "admin_security"),
        ("🧠 إدارة الذاكرة", "admin_memory_management"),
        ("🚀 حالة النشر", "deploy_status"), 
        ("❌ إغلاق اللوحة", "close_panel")
    ]
    keyboard.add(*[InlineKeyboardButton(text=text, callback_data=cb) for text, cb in buttons])
    return keyboard

def create_user_buttons():
    """ينشئ الأزرار الرئيسية للمستخدم بناءً على الإعدادات."""
    ui_conf = data_store.bot_data['ui_config']
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        (ui_conf.get('date_button_label', '📅 اليوم هجري'), "hijri_today"),
        (ui_conf.get('time_button_label', '⏰ الساعة الان'), "live_time"),
        (ui_conf.get('reminder_button_label', '💡 تذكير يومي'), "daily_reminder")
    ]
    keyboard.add(*[InlineKeyboardButton(text=text, callback_data=cb) for text, cb in buttons])
    return keyboard

def get_menu_keyboard(menu_type):
    """ينشئ القوائم الفرعية داخل لوحة التحكم مع زر رجوع دائم."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    cfg = data_store.bot_data['bot_settings']

    buttons_map = {
        "admin_dyn_replies": [("➕ برمجة رد جديد", "add_dyn_reply"), ("🗑️ حذف رد مبرمج", "delete_dyn_reply"), ("📝 عرض الردود", "show_dyn_replies")],
        "admin_reminders": [("➕ إضافة تذكير", "add_reminder"), ("🗑️ حذف تذكير", "delete_reminder"), ("📝 عرض التذكيرات", "show_reminders")],
        "admin_channel": [("➕ إضافة رسالة تلقائية", "add_channel_msg"), ("🗑️ حذف رسالة تلقائية", "delete_channel_msg"), ("📝 عرض الرسائل", "show_channel_msgs"), ("📤 نشر فوري", "instant_channel_post"), ("⏰ جدولة رسالة محددة", "schedule_post")],
        "admin_channel_settings": [("🆔 تعديل ID القناة", "set_channel_id"), ("⏰ تعديل فترة النشر التلقائي", "set_schedule_interval")],
        "admin_ban": [("🚫 حظر مستخدم", "ban_user"), ("✅ إلغاء حظر", "unban_user"), ("📋 قائمة المحظورين", "show_banned")],
        "admin_broadcast": [("📤 إرسال رسالة جماعية", "send_broadcast")],
        "admin_customize_ui": [("✏️ تعديل زر التاريخ", "edit_date_button"), ("✏️ تعديل زر الساعة", "edit_time_button"), ("✏️ تعديل زر التذكير", "edit_reminder_button"), ("👋 تعديل رسالة الترحيب", "edit_welcome_msg"), ("💬 تعديل رسالة الرد", "edit_reply_msg")],
        "admin_security": [
            ("🔴 إيقاف البوت" if not cfg.get('maintenance_mode') else "🟢 تشغيل البوت", "toggle_maintenance"),
            ("🔒 تفعيل الحماية" if not cfg.get('content_protection') else "🔓 إلغاء الحماية", "toggle_protection"),
            ("🔧 إعدادات منع التكرار", "spam_settings"), ("⏳ إعدادات التباطؤ", "slow_mode_settings"),
            ("🖼️ إدارة الوسائط", "media_settings"),
        ],
        "media_settings": [("➕ السماح بنوع وسائط", "add_media_type"), ("➖ منع نوع وسائط", "remove_media_type")],
        "admin_memory_management": [("🗑️ مسح بيانات مستخدم", "clear_user_data"), ("🧹 مسح ذاكرة Spam", "clear_spam_cache")]
    }
    
    buttons = [InlineKeyboardButton(text=text, callback_data=cb) for text, cb in buttons_map.get(menu_type, [])]
    if buttons: keyboard.add(*buttons)
    
    # Add the correct back button
    back_button_target = "admin_security" if menu_type == "media_settings" else "back_to_main"
    keyboard.add(InlineKeyboardButton(text="🔙 الرجوع", callback_data=back_button_target))

    return keyboard

def back_kb(callback_data: str = "back_to_main"):
    """Creates a simple keyboard with a single 'Back' button."""
    return InlineKeyboardMarkup().add(InlineKeyboardButton(text="🔙 الرجوع", callback_data=callback_data))

def add_another_kb(add_callback: str, back_callback: str):
    """Creates a keyboard with 'Add Another' and 'Back' buttons."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton(text="➕ إضافة آخر", callback_data=add_callback))
    keyboard.add(InlineKeyboardButton(text="🔙 الرجوع للقائمة", callback_data=back_callback))
    return keyboard
