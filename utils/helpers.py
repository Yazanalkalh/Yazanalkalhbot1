import datetime
import random
import pytz
from hijri_converter import convert
from babel.dates import format_date
import data_store
from loader import bot
from config import ADMIN_CHAT_ID
from aiogram import types # Make sure 'types' is imported

# This file contains helper functions. The date/time functions are now fully timezone-aware.

def get_hijri_date_str():
    """
    UPGRADED: Returns a formatted Hijri and Gregorian date string.
    This function is now timezone-aware and uses the timezone set by the admin.
    """
    try:
        # 1. Get the timezone name from data_store, with a safe fallback.
        #    Using 'Asia/Riyadh' as it's a common timezone in the region (UTC+3)
        tz_name = data_store.bot_data.get('ui_config', {}).get('timezone', 'Asia/Riyadh')
        user_tz = pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        # If the admin enters a wrong timezone name, fall back to a safe default.
        user_tz = pytz.timezone('Asia/Riyadh')

    # 2. Get the current time IN THE USER'S TIMEZONE. This is the critical step.
    now_in_user_tz = datetime.datetime.now(user_tz)
    
    # 3. Use THIS date, which is correct for the user, not the server's date.
    today = now_in_user_tz.date()

    # The rest of the logic is the same, but now it uses the correct 'today'.
    hijri_date = convert.Gregorian(today.year, today.month, today.day).to_hijri()
    
    day_name = format_date(today, "EEEE", locale="ar")
    hijri_str = f"{hijri_date.day} {hijri_date.month_name('ar')} {hijri_date.year}هـ"
    gregorian_str = format_date(today, "d MMMM yyyy", locale="ar") + " م"

    return (f"<b>اليوم :</b> {day_name}\n"
            f"<b>التاريخ :</b> {hijri_str}\n"
            f"<b>الموافق :</b> {gregorian_str}")

def get_live_time_str():
    """
    UPGRADED: Returns a formatted time string for the configured timezone.
    Added a more descriptive timezone name.
    """
    try:
        tz_name = data_store.bot_data.get('ui_config', {}).get('timezone', 'Asia/Riyadh')
        user_tz = pytz.timezone(tz_name)
        # Get a more user-friendly location name from the timezone
        location_name = tz_name.split('/')[-1].replace('_', ' ')
    except pytz.UnknownTimeZoneError:
        user_tz = pytz.timezone('Asia/Riyadh')
        location_name = "Riyadh"

    now = datetime.datetime.now(user_tz)
    time_str = now.strftime("%I:%M:%S %p") # Added seconds for more accuracy
    am_pm_arabic = "صباحاً" if now.strftime("%p") == "AM" else "مساءً"
    
    # Replaced hardcoded city with the dynamic one from the timezone
    return f"<b>الساعة الآن :</b>\n{time_str.replace('AM', am_pm_arabic).replace('PM', am_pm_arabic)} (بتوقيت {location_name})"

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
    user_info = f"📩 <b>رسالة جديدة من:</b> {message.from_user.full_name}\n<b>ID:</b> <code>{message.from_user.id}</code>"
    try:
        # Send user info first
        admin_info_msg = await bot.send_message(ADMIN_CHAT_ID, user_info)
        # Then forward the actual message
        fwd_msg = await message.forward(ADMIN_CHAT_ID)
        # Link admin's forwarded message to the user for easy reply
        data_store.forwarded_message_links[fwd_msg.message_id] = {
            "user_id": message.from_user.id,
            "original_message_id": message.message_id
        }
    except Exception as e:
        print(f"FORWARDING ERROR: {e}")


