import datetime
import random
import pytz
from hijri_converter import convert
from babel.dates import format_date
import data_store
from loader import bot
from config import ADMIN_CHAT_ID
from aiogram import types

# This file contains helper functions. The timezone logic is now more robust and intelligent.

def get_hijri_date_str():
    """
    Returns a formatted Hijri and Gregorian date string, fully timezone-aware.
    """
    try:
        tz_name = data_store.bot_data.get('ui_config', {}).get('timezone', 'Asia/Riyadh')
        # NEW: Alias dictionary to handle common variations
        tz_aliases = { "Asia/Sana'a": "Asia/Sanaa" }
        corrected_tz_name = tz_aliases.get(tz_name, tz_name)
        user_tz = pytz.timezone(corrected_tz_name)
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

def get_live_time_str():
    """
    UPGRADED: Returns a formatted time string and translates common city names into Arabic.
    """
    try:
        tz_name = data_store.bot_data.get('ui_config', {}).get('timezone', 'Asia/Riyadh')
        # NEW: Alias dictionary to handle common variations
        tz_aliases = { "Asia/Sana'a": "Asia/Sanaa" }
        corrected_tz_name = tz_aliases.get(tz_name, tz_name)
        user_tz = pytz.timezone(corrected_tz_name)
        location_name_en = corrected_tz_name.split('/')[-1].replace('_', ' ')
    except pytz.UnknownTimeZoneError:
        user_tz = pytz.timezone('Asia/Riyadh')
        location_name_en = "Riyadh"

    # UPGRADED: Translation dictionary now includes the official name 'Sanaa'
    translation_dict = {
        "Riyadh": "الرياض",
        "Aden": "عدن",
        "Sanaa": "صنعاء", # The official key for translation
        "Cairo": "القاهرة",
        "Dubai": "دبي",
        "Mecca": "مكة المكرمة"
    }
    location_name_ar = translation_dict.get(location_name_en, location_name_en)

    now = datetime.datetime.now(user_tz)
    time_str = now.strftime("%I:%M:%S %p")
    am_pm_arabic = "صباحاً" if now.strftime("%p") == "AM" else "مساءً"
    
    return f"<b>الساعة الآن :</b>\n{time_str.replace('AM', am_pm_arabic).replace('PM', am_pm_arabic)} (بتوقيت {location_name_ar})"

# --- Unchanged functions below ---

def get_random_reminder():
    reminders = data_store.bot_data.get('reminders', [])
    return random.choice(reminders) if reminders else "لا توجد تذكيرات متاحة حالياً."

def format_welcome_message(message_text, user):
    return (message_text
            .replace("#name_user", f"<a href='tg://user?id={user.id}'>{user.first_name}</a>")
            .replace("#username", f"@{user.username}" if user.username else user.first_name)
            .replace("#name", user.first_name)
            .replace("#id", str(user.id)))

async def forward_to_admin(message: types.Message):
    user_info = f"📩 <b>رسالة جديدة من:</b> {message.from_user.full_name}\n<b>ID:</b> <code>{message.from_user.id}</code>"
    try:
        await bot.send_message(ADMIN_CHAT_ID, user_info)
        fwd_msg = await message.forward(ADMIN_CHAT_ID)
        data_store.forwarded_message_links[fwd_msg.message_id] = {
            "user_id": message.from_user.id,
            "original_message_id": message.message_id
        }
    except Exception as e:
        print(f"FORWARDING ERROR: {e}")
