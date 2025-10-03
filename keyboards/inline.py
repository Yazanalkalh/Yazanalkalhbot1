from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data_store import bot_data

def create_admin_panel():
    """ينشئ لوحة التحكم الرئيسية للمشرف."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        ("📝 الردود الديناميكية", "admin_dyn_replies"), ("💭 إدارة التذكيرات", "admin_reminders"),
        ("📢 إدارة القناة", "admin_channel"), ("🚫 إدارة الحظر", "admin_ban"),
        ("📤 النشر للجميع", "admin_broadcast"), ("📊 إحصائيات البوت", "admin_stats"),
        ("🎨 تخصيص واجهة البوت", "admin_customize_ui"), ("🧠 إدارة الذاكرة", "admin_memory_management"),
        ("🚀 حالة النشر", "deploy_status"), ("❌ إغلاق اللوحة", "close_panel")
    ]
    keyboard.add(*[InlineKeyboardButton(text=text, callback_data=cb) for text, cb in buttons])
    return keyboard

def create_user_buttons():
    """ينشئ الأزرار الرئيسية للمستخدم بناءً على الإعدادات."""
    ui_conf = bot_data['ui_config']
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        (ui_conf.get('date_button_label', '📅 اليوم هجري'), "hijri_today"),
        (ui_conf.get('time_button_label', '⏰ الساعة الان'), "live_time"),
        (ui_conf.get('reminder_button_label', '💡 تذكير يومي'), "daily_reminder")
    ]
    keyboard.add(*[InlineKeyboardButton(text=text, callback_data=cb) for text, cb in buttons])
    return keyboard

def get_menu_keyboard(menu_type):
    """ينشئ القوائم الفرعية داخل لوحة التحكم."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    is_media_allowed = bot_data['bot_config'].get('allow_media', False)
    
    buttons_map = {
        "admin_dyn_replies": [("➕ برمجة رد جديد", "add_dyn_reply"), ("🗑️ حذف رد مبرمج", "delete_dyn_reply"), ("📝 عرض الردود", "show_dyn_replies")],
        "admin_reminders": [("➕ إضافة تذكير", "add_reminder"), ("🗑️ حذف تذكير", "delete_reminder"), ("📝 عرض التذكيرات", "show_reminders")],
        "admin_channel": [("➕ إضافة رسالة تلقائية", "add_channel_msg"), ("🗑️ حذف رسالة تلقائية", "delete_channel_msg"), ("📝 عرض الرسائل", "show_channel_msgs"), ("📤 نشر فوري", "instant_channel_post"), ("⏰ جدولة رسالة محددة", "schedule_post")],
        "admin_ban": [("🚫 حظر مستخدم", "ban_user"), ("✅ إلغاء حظر", "unban_user"), ("📋 قائمة المحظورين", "show_banned")],
        "admin_customize_ui": [("✏️ تعديل زر التاريخ", "edit_date_button"), ("✏️ تعديل زر الساعة", "edit_time_button"), ("✏️ تعديل زر التذكير", "edit_reminder_button"), ("👋 تعديل رسالة الترحيب", "edit_welcome_msg"), ("💬 تعديل رسالة الرد", "edit_reply_msg"), ("🔒 إدارة الوسائط", "admin_media_settings")],
        "admin_media_settings": [("🔒 منع الوسائط" if is_media_allowed else "🔓 السماح بالوسائط", "toggle_media"), ("✏️ تعديل رسالة الرفض", "edit_media_reject_msg")],
        "admin_memory_management": [("🗑️ مسح بيانات مستخدم", "clear_user_data"), ("🧹 مسح ذاكرة Spam", "clear_spam_cache")]
    }
    buttons = [InlineKeyboardButton(text=text, callback_data=cb) for text, cb in buttons_map.get(menu_type, [])]
    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton(text="🔙 العودة للوحة التحكم", callback_data="back_to_main"))
    return keyboard

def back_kb(callback_data: str = "back_to_main"):
    """ينشئ زر 'عودة' بسيط."""
    return InlineKeyboardMarkup().add(InlineKeyboardButton(text="🔙 العودة", callback_data=callback_data))
