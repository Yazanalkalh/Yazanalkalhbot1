import datetime
import random
import pytz
from hijri_converter import convert
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import data_store
from loader import bot
from config import ADMIN_CHAT_ID

forwarded_message_links = {}

# --- دوال إنشاء الأزرار ---
def create_admin_panel():
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
    """
    تم تحديث هذه الدالة لحذف زر "من المطور".
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        ("📅 اليوم هجري", "hijri_today"),
        ("⏰ الساعة والتاريخ", "live_time"),
        ("💡 تذكير يومي", "daily_reminder")
    ]
    keyboard.add(*[InlineKeyboardButton(text=text, callback_data=cb) for text, cb in buttons])
    return keyboard

# --- دوال مساعدة ---
def is_banned(user_id):
    return user_id in data_store.BANNED_USERS

def get_hijri_date():
    """
    تم تحديث هذه الدالة بالكامل لتطابق التنسيق الجديد المطلوب.
    """
    try:
        today = datetime.date.today()
        hijri = convert.Gregorian(today.year, today.month, today.day).to_hijri()

        weekdays_ar = {
            0: "الإثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس",
            4: "الجمعة", 5: "السبت", 6: "الأحد"
        }
        day_name_ar = weekdays_ar[today.weekday()]

        hijri_date_str = f"{hijri.day} {hijri.month_name()} {hijri.year} هـ"
        gregorian_date_str = today.strftime('%d / %m / %Y م')

        result = (
            f"**اليوم :** {day_name_ar}\n"
            f"**التاريخ هجري بالغة العربية :** {hijri_date_str}\n"
            f"**الموافق بالميلادي عربي :** {gregorian_date_str}"
        )
        return result
    except Exception as e:
        print(f"Error in get_hijri_date: {e}")
        return "عذراً، حدث خطأ أثناء جلب التاريخ."

def get_live_time():
    """
    تم تحديث هذه الدالة بالكامل لتعرض التوقيت بتنسيق صنعاء.
    """
    try:
        # Asia/Aden هو المعرف الرسمي لتوقيت اليمن (صنعاء)
        sanaa_tz = pytz.timezone('Asia/Aden')
        now = datetime.datetime.now(sanaa_tz)

        time_12h = now.strftime('%I:%M:%S')
        period_ar = "صباحاً" if now.strftime('%p') == "AM" else "مساءً"

        result = f"**الوقت :** {time_12h} {period_ar} بتوقيت صنعاء"
        return result
    except Exception as e:
        print(f"Error in get_live_time: {e}")
        return "عذراً، لا يمكن جلب التوقيت الحالي."

def get_daily_reminder():
    return random.choice(data_store.DAILY_REMINDERS) if data_store.DAILY_REMINDERS else "لا توجد تذكيرات متاحة."

async def forward_to_admin(message):
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


