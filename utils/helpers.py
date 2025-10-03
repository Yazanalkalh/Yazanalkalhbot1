from aiogram import types # <-- THIS IS THE MISSING LINE
import datetime
import random
import pytz
from hijri_converter import convert
from babel.dates import format_date
import data_store
from loader import bot

def get_hijri_date_str():
    """Returns a formatted Hijri and Gregorian date string in Arabic."""
    today = datetime.date.today()
    hijri_date = convert.Gregorian(today.year, today.month, today.day).to_hijri()
    
    day_name = format_date(today, "EEEE", locale="ar")
    hijri_str = f"{hijri_date.day} {hijri_date.month_name('ar')} {hijri_date.year}هـ"
    gregorian_str = format_date(today, "d MMMM yyyy", locale="ar") + " م"

    return (f"<b>اليوم :</b> {day_name}\n"
            f"<b>التاريخ :</b> {hijri_str}\n"
            f"<b>الموافق :</b> {gregorian_str}")

def get_live_time_str():
    """Returns a formatted time string for the configured timezone."""
    try:
        tz_name = data_store.bot_data['ui_config']['timezone']
        user_tz = pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        user_tz = pytz.timezone('Asia/Aden') # Fallback

    now = datetime.datetime.now(user_tz)
    time_str = now.strftime("%I:%M %p")
    am_pm_arabic = "صباحاً" if now.strftime("%p") == "AM" else "مساءً"
    
    return f"<b>الساعة الآن :</b>\n{time_str.replace('AM', am_pm_arabic).replace('PM', am_pm_arabic)} (بتوقيت صنعاء)"

def get_random_reminder():
    """Returns a random reminder."""
    reminders = data_store.bot_data.get('reminders', [])
    return random.choice(reminders) if reminders else "لا توجد تذكيرات متاحة حالياً."

def format_welcome_message(message_text, user):
    """Formats the welcome message with user-specific hashtags."""
    return (message_text
            .replace("#name_user", f"<a href='tg://user?id={user.id}'>{user.first_name}</a>")
            .replace("#username", f"@{user.username}" if user.username else user.first_name)
            .replace("#name", user.first_name)
            .replace("#id", str(user.id)))

async def forward_to_admin(message: types.Message):
    """Forwards a user's message to the admin with a special format."""
    from config import ADMIN_CHAT_ID

    user_info = f"📩 <b>رسالة جديدة من:</b> {message.from_user.full_name}\n<b>ID:</b> <code>{message.from_user.id}</code>"
    print(f"Attempting to forward message from {message.from_user.id} to admin {ADMIN_CHAT_ID}")

    try:
        # Send user info first
        await bot.send_message(ADMIN_CHAT_ID, user_info)
        # Then forward the actual message
        fwd_msg = await message.forward(ADMIN_CHAT_ID)
        # Link admin's forwarded message to the user for easy reply
        data_store.forwarded_message_links[fwd_msg.message_id] = {
            "user_id": message.from_user.id,
            "original_message_id": message.message_id
        }
        print("Message forwarded successfully.")
    except Exception as e:
        print(f"CRITICAL FORWARDING ERROR: {e}")
