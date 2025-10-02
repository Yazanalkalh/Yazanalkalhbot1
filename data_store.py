import datetime
from database import load_data_from_db, save_data_to_db

# --- تحميل البيانات والمتغيرات العامة ---
bot_data = load_data_from_db()
start_time = datetime.datetime.now()

# قوائم البيانات التي يتم تحديثها باستمرار
USERS_LIST = set(bot_data.get("users", []))
BANNED_USERS = set(bot_data.get("banned_users", []))
AUTO_REPLIES = bot_data.get("auto_replies", {})
DAILY_REMINDERS = bot_data.get("daily_reminders", [])
CHANNEL_MESSAGES = bot_data.get("channel_messages", [])

# متغيرات مؤقتة (لا تحفظ في قاعدة البيانات)
user_threads = {}
user_message_count = {}
silenced_users = {}

def save_all_data():
    """دالة مركزية لحفظ كل البيانات المتغيرة"""
    bot_data['users'] = list(USERS_LIST)
    bot_data['banned_users'] = list(BANNED_USERS)
    bot_data['auto_replies'] = AUTO_REPLIES
    bot_data['daily_reminders'] = DAILY_REMINDERS
    bot_data['channel_messages'] = CHANNEL_MESSAGES
    save_data_to_db(bot_data)
