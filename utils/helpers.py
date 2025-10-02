import datetime
import random
import pytz
from hijri_converter import convert
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import data_store
from loader import bot
from config import ADMIN_CHAT_ID

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
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        ("📅 اليوم هجري", "hijri_today"), ("⏰ الساعة والتاريخ", "live_time"),
        ("💡 تذكير يومي", "daily_reminder"), ("👨‍💻 من المطور", "from_developer")
    ]
    keyboard.add(*[InlineKeyboardButton(text=text, callback_data=cb) for text, cb in buttons])
    return keyboard

# --- دوال مساعدة ---
def is_banned(user_id):
    return user_id in data_store.BANNED_USERS

def get_hijri_date():
    try:
        today = datetime.date.today()
        hijri = convert.Gregorian(today.year, today.month, today.day).to_hijri()
        return f"**التاريخ الهجري:** {hijri.day} {hijri.month_name()} {hijri.year} هـ"
    except Exception:
        return "عذراً، لا يمكن جلب التاريخ الهجري حالياً."

def get_live_time():
    try:
        now = datetime.datetime.now(pytz.timezone('Asia/Riyadh'))
        return f"**التوقيت الحالي (الرياض):**\n- **الساعة:** {now.strftime('%H:%M:%S')}\n- **التاريخ:** {now.strftime('%d/%m/%Y')}"
    except Exception:
        return "عذراً، لا يمكن جلب التوقيت الحالي."

def get_daily_reminder():
    return random.choice(data_store.DAILY_REMINDERS) if data_store.DAILY_REMINDERS else "لا توجد تذكيرات متاحة."

async def forward_to_admin(message):
    try:
        user_info = f"📩 رسالة جديدة من: {message.from_user.full_name}\n**ID:** `{message.from_user.id}`"
        await bot.send_message(ADMIN_CHAT_ID, user_info)
        fw_msg = await message.forward(ADMIN_CHAT_ID)
        data_store.user_threads[fw_msg.forward_from.id] = message.message_id
    except Exception as e:
        print(f"فشل إعادة توجيه الرسالة: {e}")
