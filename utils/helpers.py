import datetime
import random
import pytz
from hijri_converter import convert

import data_store
from loader import bot
from config import ADMIN_CHAT_ID

# قاموس لتخزين الروابط بين الرسائل الموجهة والمستخدمين للرد عليها
forwarded_message_links = {}

def is_banned(user_id):
    """يتحقق مما إذا كان المستخدم محظوراً."""
    return user_id in data_store.BANNED_USERS

def get_hijri_date():
    """ينشئ نص التاريخ بالتنسيق المطلوب."""
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
        print(f"Error in get_hijri_date: {e}")
        return "عذراً، حدث خطأ أثناء جلب التاريخ."

def get_live_time():
    """ينشئ نص الوقت بالتنسيق المطلوب."""
    try:
        sanaa_tz = pytz.timezone('Asia/Aden')
        now = datetime.datetime.now(sanaa_tz)
        time_12h = now.strftime('%I:%M:%S')
        period_ar = "صباحاً" if now.strftime('%p') == "AM" else "مساءً"
        return f"**الوقت :** {time_12h} {period_ar} بتوقيت صنعاء"
    except Exception as e:
        print(f"Error in get_live_time: {e}")
        return "عذراً، لا يمكن جلب التوقيت الحالي."

def get_daily_reminder():
    """يحصل على تذكير يومي عشوائي."""
    return random.choice(data_store.DAILY_REMINDERS) if data_store.DAILY_REMINDERS else "لا توجد تذكيرات متاحة."

async def forward_to_admin(message):
    """يعيد توجيه رسالة المستخدم للمشرف ويسجل بيانات الربط للرد."""
    try:
        fw_msg = await message.forward(ADMIN_CHAT_ID)
        forwarded_message_links[fw_msg.message_id] = {
            "user_id": message.from_user.id,
            "original_message_id": message.message_id
        }
    except Exception as e:
        print(f"فشل إعادة توجيه الرسالة من {message.from_user.id}: {e}")
        fallback_text = (
            f"📩 **فشل توجيه رسالة من:** {message.from_user.full_name} (`{message.from_user.id}`)\n\n"
            f"**محتوى الرسالة:**\n{message.text or '[محتوى غير نصي]'}\n\n"
            f"⚠️ **تنبيه:** لا يمكنك الرد على هذه الرسالة مباشرة."
        )
        await bot.send_message(ADMIN_CHAT_ID, fallback_text)
