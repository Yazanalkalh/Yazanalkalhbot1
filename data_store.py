import datetime
from database import load_all_data, save_all_data as db_save

# القالب الافتراضي الكامل لإعدادات البوت
DEFAULT_SETTINGS = {
    "users": [],
    "banned_users": [],
    "reminders": [
        "🌅 سبحان الله وبحمده، سبحان الله العظيم.",
        "🤲 اللهم أعني على ذكرك وشكرك وحسن عبادتك.",
        "💎 لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير."
    ],
    "channel_messages": [
        "🌙 بسم الله نبدأ يوماً جديداً\n\n💎 قال تعالى: {وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا}",
        "🌟 تذكير إيماني\n\n📖 قال رسول الله ﷺ: (إن الله جميل يحب الجمال)"
    ],
    "dynamic_replies": {
        "مرحبا": "أهلاً وسهلاً بك!",
        "السلام عليكم": "وعليكم السلام ورحمة الله وبركاته."
    },
    "scheduled_posts": [],
    "bot_config": {
        "channel_id": "",
        "schedule_interval_seconds": 86400,
        "allow_media": False,
        "welcome_message": "👋 **أهلاً بك، #name!**\n\nهذا البوت مخصص للتواصل مع فريق القناة. أرسل استفسارك وسيتم الرد عليك.",
        "reply_message": "✅ **تم استلام رسالتك!** سيقوم الفريق بمراجعتها والرد عليك.",
        "media_reject_message": "❌ **عذراً،** يُسمح بإرسال الرسائل النصية فقط حالياً."
    },
    "ui_config": {
        "date_button_label": "📅 اليوم هجري",
        "time_button_label": "⏰ الساعة الان",
        "reminder_button_label": "💡 تذكير يومي",
        "timezone": "Asia/Aden"
    }
}

# --- تهيئة البيانات عند بدء التشغيل ---
# هذا هو المتغير الرئيسي الذي سيستخدمه كل البوت
bot_data = load_all_data()
start_time = datetime.datetime.now()

# متغيرات مؤقتة (لا يتم حفظها في قاعدة البيانات)
forwarded_message_links = {}
user_message_count = {}
silenced_users = {}

# --- دالة الحفظ المركزية ---
def save_data():
    """
    دالة مساعدة لحفظ الحالة الحالية لـ bot_data في قاعدة البيانات.
    """
    db_save(bot_data)
