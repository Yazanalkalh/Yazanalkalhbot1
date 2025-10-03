import datetime

# This is the master template for all bot settings.
# It ensures the bot always has a value to fall back on.
DEFAULT_SETTINGS = {
    "_id": "main_bot_config",
    "users": [],
    "banned_users": [],
    "reminders": [
        "🌅 سبحان الله وبحمده، سبحان الله العظيم.",
        "🤲 اللهم أعني على ذكرك وشكرك وحسن عبادتك.",
    ],
    "channel_messages": [
        "🌙 بسم الله نبدأ يوماً جديداً\n\n💎 قال تعالى: {وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا}",
    ],
    "dynamic_replies": {
        "مرحبا": "أهلاً وسهلاً بك!",
        "السلام عليكم": "وعليكم السلام ورحمة الله وبركاته."
    },
    "scheduled_posts": [],
    "bot_settings": {
        "maintenance_mode": False,
        "maintenance_message": "عذراً، البوت قيد الصيانة حالياً. سنعود قريباً.",
        "content_protection": False,
        "slow_mode_seconds": 0,
        "spam_message_limit": 5,
        "spam_time_window": 60,
        "allowed_media_types": ["text"], # Default: only text is allowed
        "channel_id": "",
        "schedule_interval_seconds": 86400,
        "welcome_message": "👋 **أهلاً بك، #name!**\n\nهذا البوت مخصص للتواصل مع فريق القناة.",
        "reply_message": "✅ **تم استلام رسالتك!** سيقوم الفريق بمراجعتها.",
        "media_reject_message": "❌ **عذراً،** هذا النوع من الرسائل غير مسموح به حالياً."
    },
    "ui_config": {
        "date_button_label": "📅 اليوم هجري",
        "time_button_label": "⏰ الساعة الان",
        "reminder_button_label": "💡 تذكير يومي",
        "timezone": "Asia/Aden"
    }
}

# Initial load of data
from database import load_all_data, save_all_data as db_save
bot_data = load_all_data()

# Global runtime variables (not saved in DB)
start_time = datetime.datetime.now()
forwarded_message_links = {}
user_message_count = {}
silenced_users = {}
user_last_message_time = {}

def save_data():
    """A centralized function to save data."""
    db_save(bot_data)
