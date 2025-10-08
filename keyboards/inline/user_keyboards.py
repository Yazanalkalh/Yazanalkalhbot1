from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# ✅ تم الإصلاح: لا يوجد data_store، نستخدم قاعدة البيانات مباشرة
from utils import database

def create_user_buttons() -> InlineKeyboardMarkup:
    """
    ✅ تم الإصلاح: تنشئ لوحة المفاتيح بناءً على أحدث إعدادات الواجهة من قاعدة البيانات.
    """
    # نقوم بجلب إعدادات الواجهة المحدثة مباشرة من قاعدة البيانات
    # نوفر قيمًا افتراضية قوية في حال لم تكن الإعدادات موجودة
    ui_config = database.get_setting('ui_config', {})
    
    date_label = ui_config.get('date_button_label', '📅 التاريخ')
    time_label = ui_config.get('time_button_label', '⏰ الساعة الان')
    reminder_label = ui_config.get('reminder_button_label', '💡 تذكير يومي')
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text=date_label, callback_data="show_date"),
        InlineKeyboardButton(text=time_label, callback_data="show_time"),
        InlineKeyboardButton(text=reminder_label, callback_data="show_reminder")
    )
    return keyboard
