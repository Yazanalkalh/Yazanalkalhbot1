import datetime
import pytz
from hijri_converter import convert
from babel.dates import format_date
from aiogram import types
from loader import bot
from config import ADMIN_CHAT_ID
from utils import database

def get_hijri_date_str():
    """Returns a formatted Hijri and Gregorian date string."""
    try:
        tz_name = database.get_setting('ui.timezone', 'Asia/Riyadh')
        user_tz = pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        user_tz = pytz.timezone('Asia/Riyadh')

    today = datetime.datetime.now(user_tz).date()
    hijri_date = convert.Gregorian(today.year, today.month, today.day).to_hijri()
    
    day_name = format_date(today, "EEEE", locale="ar")
    hijri_str = f"{hijri_date.day} {hijri_date.month_name('ar')} {hijri_date.year}هـ"
    gregorian_str = format_date(today, "d MMMM yyyy", locale="ar") + " م"

    return (f"<b>اليوم:</b> {day_name}\n"
            f"<b>التاريخ:</b> {hijri_str}\n"
            f"<b>الموافق:</b> {gregorian_str}")

def get_live_time_str():
    """Returns a formatted time string based on the configured timezone."""
    try:
        tz_name = database.get_setting('ui.timezone', 'Asia/Riyadh')
        user_tz = pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        user_tz = pytz.timezone('Asia/Riyadh')
    
    now = datetime.datetime.now(user_tz)
    time_str = now.strftime("%I:%M:%S %p")
    am_pm_arabic = "صباحاً" if now.strftime("%p") == "AM" else "مساءً"
    
    return f"<b>الساعة الآن:</b>\n{time_str.replace('AM', am_pm_arabic).replace('PM', am_pm_arabic)}"

async def forward_to_admin(message: types.Message):
    """Forwards a user's message to the admin and saves a link for replying."""
    user_info = f"📩 <b>رسالة جديدة من:</b> {message.from_user.full_name}\n<b>ID:</b> <code>{message.from_user.id}</code>"
    try:
        await bot.send_message(ADMIN_CHAT_ID, user_info)
        fwd_msg = await message.forward(ADMIN_CHAT_ID)
        # Save the link between the forwarded message and the original
        database.save_forwarded_link(fwd_msg.message_id, message.from_user.id, message.message_id)
    except Exception as e:
        print(f"FORWARDING ERROR: {e}")
