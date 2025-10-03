import datetime
import random
import pytz
from hijri_converter import convert
from aiogram import types
import data_store
from loader import bot
from config import ADMIN_CHAT_ID

def is_banned(user_id):
    """يتحقق مما إذا كان المستخدم محظوراً."""
    return user_id in data_store.bot_data['banned_users']

def get_hijri_date():
    """ينشئ نص التاريخ بناءً على الإعدادات."""
    try:
        today = datetime.date.today()
        hijri = convert.Gregorian(today.year, today.month, today.day).to_hijri()
        weekdays_ar = {0: "الإثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"}
        day_name_ar = weekdays_ar[today.weekday()]
        gregorian_months_ar = {1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"}
        gregorian_month_name_ar = gregorian_months_ar[today.month]
        hijri_date_str = f"{hijri.day} {hijri.month_name()} {hijri.year}هـ"
        gregorian_date_str = f"{today.day} {gregorian_month_name_ar} {today.year} م"
        return f"**اليوم :** {day_name_ar}\n**التاريخ :** {hijri_date_str}\n**الموافق :** {gregorian_date_str}"
    except Exception as e:
        return f"عذراً، حدث خطأ: {e}"

def get_live_time():
    """ينشئ نص الوقت بناءً على المنطقة الزمنية المحفوظة."""
    try:
        timezone_str = data_store.bot_data['ui_config'].get('timezone', 'Asia/Aden')
        target_tz = pytz.timezone(timezone_str)
        now = datetime.datetime.now(target_tz)
        time_12h = now.strftime('%I:%M:%S')
        period_ar = "صباحاً" if now.strftime('%p') == "AM" else "مساءً"
        return f"**الوقت :** {time_12h} {period_ar} بتوقيت صنعاء"
    except Exception as e:
        return f"عذراً، حدث خطأ: {e}"

def get_daily_reminder():
    """يحصل على تذكير يومي عشوائي."""
    reminders = data_store.bot_data.get('reminders', [])
    return random.choice(reminders) if reminders else "لا توجد تذكيرات حالياً."

async def forward_to_admin(message: types.Message):
    """يعيد توجيه رسالة المستخدم للمشرف ويسجل بيانات الربط للرد."""
    try:
        fw_msg = await message.forward(ADMIN_CHAT_ID)
        data_store.forwarded_message_links[fw_msg.message_id] = {
            "user_id": message.from_user.id,
            "original_message_id": message.message_id
        }
    except Exception as e:
        print(f"Failed to forward message from {message.from_user.id}: {e}")

def process_klisha(text: str, user: types.User) -> str:
    """يعالج الهاشتاقات في النص ويستبدلها بمعلومات المستخدم."""
    if not text: return ""
    return text.replace("#name_user", user.get_mention(as_html=True))\
               .replace("#username", f"@{user.username}" if user.username else user.full_name)\
               .replace("#name", user.full_name)\
               .replace("#id", str(user.id))
