import datetime
import random
import pytz
from hijri_converter import convert
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import load_data

# --- تحميل البيانات والمتغيرات العامة ---
bot_data = load_data()
start_time = datetime.datetime.now()

# قوائم البيانات التي يتم تحديثها باستمرار
USERS_LIST = set(bot_data.get("users", []))
BANNED_USERS = set(bot_data.get("banned_users", []))
AUTO_REPLIES = bot_data.get("auto_replies", {})
DAILY_REMINDERS = bot_data.get("daily_reminders", [])
CHANNEL_MESSAGES = bot_data.get("channel_messages", [])

# متغيرات مؤقتة (لا تحفظ في قاعدة البيانات)
user_messages = {}
user_threads = {}
user_message_count = {}
silenced_users = {}

# --- دوال إنشاء الأزرار ---
def create_admin_panel():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(text="📝 إدارة الردود", callback_data="admin_replies"),
        InlineKeyboardButton(text="💭 إدارة التذكيرات", callback_data="admin_reminders"),
        InlineKeyboardButton(text="📢 رسائل القناة", callback_data="admin_channel"),
        InlineKeyboardButton(text="🚫 إدارة الحظر", callback_data="admin_ban"),
        InlineKeyboardButton(text="📤 النشر للجميع", callback_data="admin_broadcast"),
        InlineKeyboardButton(text="📊 إحصائيات البوت", callback_data="admin_stats"),
        InlineKeyboardButton(text="⚙️ إعدادات القناة", callback_data="admin_channel_settings"),
        InlineKeyboardButton(text="💬 إعدادات الرسائل", callback_data="admin_messages_settings"),
        InlineKeyboardButton(text="🔒 إدارة الوسائط", callback_data="admin_media_settings"),
        InlineKeyboardButton(text="🧠 إدارة الયોاكرة", callback_data="admin_memory_management"),
        InlineKeyboardButton(text="🚀 حالة النشر", callback_data="deploy_status"),
        InlineKeyboardButton(text="❌ إغلاق اللوحة", callback_data="close_panel")
    ]
    keyboard.add(*buttons)
    return keyboard

def create_user_buttons():
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton(text="📅 اليوم هجري", callback_data="hijri_today"),
        InlineKeyboardButton(text="⏰ الساعة والتاريخ", callback_data="live_time"),
        InlineKeyboardButton(text="💡 تذكير يومي", callback_data="daily_reminder"),
        InlineKeyboardButton(text="👨‍💻 من المطور", callback_data="from_developer")
    ]
    keyboard.add(*buttons)
    return keyboard

# --- دوال مساعدة ---
def is_banned(user_id):
    return user_id in BANNED_USERS
