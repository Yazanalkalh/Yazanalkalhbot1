import datetime
import random
import pytz
from hijri_converter import convert
from babel.dates import format_date
# ✅ تم الإصلاح: لا يوجد data_store، نستخدم قاعدة البيانات والدوال الأخرى مباشرة
from . import database
from loader import bot
from config import ADMIN_CHAT_ID
from aiogram import types

def get_hijri_date_str() -> str:
    """
    ✅ تم الإصلاح: تجلب المنطقة الزمنية المحدثة مباشرة من قاعدة البيانات.
    """
    try:
        # نقرأ أحدث منطقة زمنية من قاعدة البيانات
        tz_name = database.get_setting('ui_config', {}).get('timezone', 'Asia/Riyadh')
        user_tz = pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        user_tz = pytz.timezone('Asia/Riyadh')

    now_in_user_tz = datetime.datetime.now(user_tz)
    today = now_in_user_tz.date()

    hijri_date = convert.Gregorian(today.year, today.month, today.day).to_hijri()
    
    day_name = format_date(today, "EEEE", locale="ar")
    hijri_str = f"{hijri_date.day} {hijri_date.month_name('ar')} {hijri_date.year}هـ"
    gregorian_str = format_date(today, "d MMMM yyyy", locale="ar") + " م"

    return (f"<b>اليوم :</b> {day_name}\n"
            f"<b>التاريخ :</b> {hijri_str}\n"
            f"<b>الموافق :</b> {gregorian_str}")

def get_live_time_str() -> str:
    """
    ✅ تم الإصلاح: تجلب المنطقة الزمنية المحدثة مباشرة من قاعدة البيانات.
    """
    try:
        tz_name = database.get_setting('ui_config', {}).get('timezone', 'Asia/Riyadh')
        user_tz = pytz.timezone(tz_name)
        location_name_en = tz_name.split('/')[-1].replace('_', ' ')
    except pytz.UnknownTimeZoneError:
        user_tz = pytz.timezone('Asia/Riyadh')
        location_name_en = "Riyadh"

    translation_dict = {
        "Riyadh": "الرياض", "Aden": "صنعاء", "Cairo": "القاهرة",
        "Dubai": "دبي", "Mecca": "مكة المكرمة"
    }
    location_name_ar = translation_dict.get(location_name_en, location_name_en)

    now = datetime.datetime.now(user_tz)
    time_str = now.strftime("%I:%M:%S %p")
    am_pm_arabic = "صباحاً" if now.strftime("%p") == "AM" else "مساءً"
    
    return f"<b>الساعة الآن :</b>\n{time_str.replace('AM', am_pm_arabic).replace('PM', am_pm_arabic)} (بتوقيت {location_name_ar})"

def get_random_reminder() -> str:
    """
    ✅ تم الإصلاح: تجلب قائمة التذكيرات المحدثة مباشرة من قاعدة البيانات.
    """
    reminders = database.get_all_reminders()
    return random.choice(reminders) if reminders else "لا توجد تذكيرات متاحة حالياً."

def format_welcome_message(message_text, user: types.User) -> str:
    """(لا تغييرات هنا، هذه الدالة سليمة)"""
    return (message_text
            .replace("#name_user", f"<a href='tg://user?id={user.id}'>{user.first_name}</a>")
            .replace("#username", f"@{user.username}" if user.username else user.first_name)
            .replace("#name", user.first_name)
            .replace("#id", str(user.id)))

async def forward_to_admin(message: types.Message):
    """
    ✅ تم الإصلاح: تسجل رابط الرسالة المحولة في قاعدة البيانات لضمان عدم فقدانه.
    """
    user_info = f"📩 <b>رسالة جديدة من:</b> {message.from_user.full_name}\n<b>ID:</b> <code>{message.from_user.id}</code>"
    try:
        await bot.send_message(ADMIN_CHAT_ID, user_info)
        fwd_msg = await message.forward(ADMIN_CHAT_ID)
        
        # نسجل الرابط في قاعدة البيانات بدلاً من الذاكرة المؤقتة
        database.log_forward_link(
            admin_message_id=fwd_msg.message_id,
            user_id=message.from_user.id,
            original_message_id=message.message_id
        )
    except Exception as e:
        print(f"FORWARDING ERROR: {e}")
