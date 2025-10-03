import datetime
import random
import pytz
from hijri_converter import convert
from aiogram import types

def get_hijri_date_string():
    """Generates the formatted Hijri and Gregorian date string in Arabic."""
    today = datetime.date.today()
    gregorian = convert.Gregorian(today.year, today.month, today.day)
    hijri = gregorian.to_hijri()

    hijri_months_ar = ["محرم", "صفر", "ربيع الأول", "ربيع الآخر", "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة"]
    gregorian_months_ar = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
    weekdays_ar = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]

    day_name = weekdays_ar[today.weekday()]
    hijri_month_name = hijri_months_ar[hijri.month - 1]
    gregorian_month_name = gregorian_months_ar[today.month - 1]

    return (f"<b>اليوم :</b> {day_name}\n"
            f"<b>التاريخ :</b> {hijri.day} {hijri_month_name} {hijri.year}هـ\n"
            f"<b>الموافق :</b> {today.day} {gregorian_month_name} {today.year}م")

def get_live_time_string(timezone_str: str):
    """Generates the formatted 12-hour time string for a given timezone."""
    try:
        tz = pytz.timezone(timezone_str)
        now = datetime.datetime.now(tz)
        period = "صباحاً" if now.hour < 12 else "مساءً"
        hour_12 = now.hour if now.hour == 12 else now.hour % 12
        if hour_12 == 0: hour_12 = 12 # Adjust for 12 AM
        return f"<b>الوقت :</b> {hour_12:02d}:{now.minute:02d} {period} بتوقيت صنعاء"
    except pytz.UnknownTimeZoneError:
        return "⚠️ منطقة زمنية غير صالحة."
    except Exception as e:
        return f"⚠️ حدث خطأ: {e}"
        
def process_klisha(text: str, user: types.User) -> str:
    """Replaces placeholders in a string with user information."""
    if not text: return ""
    return text.replace("#name_user", user.get_mention(as_html=True)) \
               .replace("#username", f"@{user.username}" if user.username else "لا يوجد") \
               .replace("#name", user.full_name) \
               .replace("#id", str(user.id)) 
