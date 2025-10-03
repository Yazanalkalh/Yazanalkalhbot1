import datetime
from database import load_db_data, save_db_data

# Default structure
DEFAULT_DATA = {
    "users": [],
    "banned_users": [],
    "reminders": [
        "🌅 سبحان الله وبحمده، سبحان الله العظيم.",
        "🤲 اللهم أعني على ذكرك وشكرك وحسن عبادتك.",
        "💎 لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير."
    ],
    "dynamic_replies": {},
    "channel_messages": [
        "🌙 بسم الله نبدأ يوماً جديداً\n\n💎 قال تعالى: {وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا}",
        "🌟 تذكير إيماني\n\n📖 قال رسول الله ﷺ: (إن الله جميل يحب الجمال)"
    ],
    "scheduled_posts": [],
    "bot_settings": {
        "maintenance_mode": False,
        "maintenance_message": "عذراً، البوت قيد الصيانة حالياً. سنعود قريباً.",
        "content_protection": False,
        "welcome_message": "👋 أهلاً وسهلاً بك يا #name!\n\nأنا بوت التقويم الهجري. أرسل رسالتك وسيتم الرد عليك.",
        "reply_message": "✅ تم استلام رسالتك بنجاح، شكراً لتواصلك.",
        "media_reject_message": "❌ عذراً، يُسمح فقط بالرسائل النصية.",
        "allowed_media_types": ["text"],
        "channel_id": "",
        "schedule_interval_seconds": 86400,
        "spam_message_limit": 5,
        "spam_time_window": 60,
        "slow_mode_seconds": 0
    },
    "ui_config": {
        "date_button_label": "📅 التاريخ",
        "time_button_label": "⏰ الساعة الان",
        "reminder_button_label": "💡 تذكير يومي",
        "timezone": "Asia/Aden"
    }
}

# --- Global Data Store ---
bot_data = {}
start_time = datetime.datetime.now()
# These are temporary runtime caches, not saved to DB
forwarded_message_links = {}
user_last_message_time = {}

def initialize_data():
    """Loads data from DB and merges with defaults."""
    global bot_data
    db_data = load_db_data()
    # A simple way to merge nested dictionaries
    merged_data = DEFAULT_DATA.copy()
    for key, value in db_data.items():
        if isinstance(value, dict) and key in merged_data:
            merged_data[key].update(value)
        else:
            merged_data[key] = value
    bot_data = merged_data
    print("✅ Bot data initialized.")

def save_data():
    """Saves the current bot_data state to the database."""
    # Create a copy to avoid saving runtime caches
    data_to_save = bot_data.copy()
    # Remove keys that shouldn't be persisted
    data_to_save.pop("_id", None)
    save_db_data(data_to_save)

# Initialize data on startup
initialize_data()
