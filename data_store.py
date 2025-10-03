import datetime
from utils.database import load_db_data, save_db_data

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
        "🌙 بسم الله نبدأ يوماً جديداً\n\n💎 قال تعالى: {وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا}\n\n✨ اتق الله في السر والعلن، يجعل لك من كل ضيق مخرجاً ومن كل هم فرجاً.",
        "🌟 تذكير إيماني\n\n📖 قال رسول الله ﷺ: (إن الله جميل يحب الجمال)\n\n🌸 اجعل جمال أخلاقك يعكس جمال إيمانك."
    ],
    "scheduled_posts": [],
    "bot_settings": {
        "maintenance_mode": False,
        "maintenance_message": "عذراً، البوت قيد الصيانة حالياً. سنعود قريباً.",
        "content_protection": False,
        "welcome_message": "👋 أهلًا وسهلًا بك, #name!\nأنا هنا لخدمتك.",
        "reply_message": "🌿 تم استلام رسالتك بنجاح! سيتم التواصل معك قريباً.",
        "media_reject_message": "❌ عذراً، يُسمح بالرسائل النصية فقط.",
        "allowed_media_types": ["text"],
        "spam_message_limit": 5,
        "spam_time_window": 60,
        "slow_mode_seconds": 0,
        "channel_id": "",
        "schedule_interval_seconds": 86400
    },
    "ui_config": {
        "date_button_label": "📅 التاريخ",
        "time_button_label": "⏰ الساعة الان",
        "reminder_button_label": "💡 تذكير يومي",
        "timezone": "Asia/Aden"
    }
}

bot_data = {}
start_time = datetime.datetime.now()
forwarded_message_links = {}
user_last_message_time = {}

def initialize_data():
    global bot_data
    db_data = load_db_data()
    
    merged_data = DEFAULT_DATA.copy()
    for key, value in db_data.items():
        if isinstance(value, dict) and key in merged_data:
            merged_data[key].update(value)
        else:
            merged_data[key] = value

    bot_data = merged_data
    print("✅ Bot data initialized.")

def save_data():
    save_db_data(bot_data) 
