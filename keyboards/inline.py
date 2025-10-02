from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import data_store

def create_admin_panel():
    """ينشئ لوحة التحكم الرئيسية للمشرف."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        ("📝 إدارة الردود", "admin_replies"), ("💭 إدارة التذكيرات", "admin_reminders"),
        ("📢 رسائل القناة", "admin_channel"), ("🚫 إدارة الحظر", "admin_ban"),
        ("📤 النشر للجميع", "admin_broadcast"), ("📊 إحصائيات البوت", "admin_stats"),
        ("⚙️ إعدادات القناة", "admin_channel_settings"), ("💬 إعدادات الرسائل", "admin_messages_settings"),
        ("🔒 إدارة الوسائط", "admin_media_settings"), ("🧠 إدارة الذاكرة", "admin_memory_management"),
        ("🚀 حالة النشر", "deploy_status"), ("❌ إغلاق اللوحة", "close_panel")
    ]
    keyboard.add(*[InlineKeyboardButton(text=text, callback_data=cb) for text, cb in buttons])
    return keyboard

def create_user_buttons():
    """ينشئ الأزرار الرئيسية للمستخدم العادي."""
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        ("📅 اليوم هجري", "hijri_today"),
        ("⏰ الساعة الان", "live_time"),
        ("💡 تذكير يومي", "daily_reminder")
    ]
    keyboard.add(*[InlineKeyboardButton(text=text, callback_data=cb) for text, cb in buttons])
    return keyboard

def get_menu_keyboard(menu_type):
    """ينشئ القوائم الفرعية داخل لوحة التحكم."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons_map = {
        "admin_replies": [("➕ إضافة رد", "add_reply"), ("📝 عرض الردود", "show_replies"), ("🗑️ حذف رد", "delete_reply_menu")],
        "admin_reminders": [("➕ إضافة تذكير", "add_reminder"), ("📝 عرض التذكيرات", "show_reminders"), ("🗑️ حذف تذكير", "delete_reminder_menu")],
        "admin_channel": [("➕ إضافة رسالة", "add_channel_msg"), ("📝 عرض الرسائل", "show_channel_msgs"), ("🗑️ حذف رسالة", "delete_channel_msg_menu"), ("📤 نشر فوري", "instant_channel_post")],
        "admin_ban": [("🚫 حظر مستخدم", "ban_user"), ("✅ إلغاء حظر", "unban_user"), ("📋 قائمة المحظورين", "show_banned")],
        "admin_broadcast": [("📤 إرسال رسالة جماعية", "send_broadcast")],
        "admin_channel_settings": [("🆔 تعديل ID القناة", "set_channel_id"), ("⏰ تعديل فترة النشر", "set_schedule_time")],
        "admin_messages_settings": [("👋 تعديل رسالة الترحيب", "set_welcome_msg"), ("💬 تعديل رسالة الرد", "set_reply_msg")],
        "admin_media_settings": [("🔒 منع الوسائط" if data_store.bot_data.get('allow_media') else "🔓 السماح بالوسائط", "toggle_media"), ("✏️ تعديل رسالة الرفض", "set_media_reject_msg")],
        "admin_memory_management": [("🗑️ مسح بيانات مستخدم", "clear_user_messages"), ("🧹 مسح ذاكرة Spam", "clear_temp_memory")]
    }
    buttons = [InlineKeyboardButton(text=text, callback_data=cb) for text, cb in buttons_map.get(menu_type, [])]
    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton(text="🔙 العودة للوحة التحكم", callback_data="back_to_main"))
    return keyboard

def back_kb(callback_data: str):
    """ينشئ زر "عودة" بسيط."""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="🔙 العودة", callback_data=callback_data))
    return keyboard

