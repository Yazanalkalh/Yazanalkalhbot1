import datetime
import random
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Attempt to import hijri_converter and pytz, handle if not installed
try:
    from hijri_converter import convert
except ImportError:
    convert = None
try:
    import pytz
except ImportError:
    pytz = None

# Import core components
from database import load_data, save_data
from loader import bot
from config import ADMIN_CHAT_ID

# --- Load initial data on startup ---
bot_data = load_data()
start_time = datetime.datetime.now()

# --- Global Data Structures (loaded from DB and updated in memory) ---
USERS_LIST = set(bot_data.get("users", []))
AUTO_REPLIES = {
    "السلام عليكم": "وعليكم السلام ورحمة الله وبركاته 🌹\nأهلاً بك في بوت التقويم الهجري 🌙",
    "مرحبا": "مرحباً بك في بوت التقويم الهجري 🌙\nأهلاً وسهلاً في بيتك الثاني ✨",
    "كيف حالك": "الحمد لله بخير وعافية 🤲\nوأنت كيف حالك؟ أتمنى أن تكون بأفضل حال 🌹",
    "شكرا": "العفو حبيبي 🌹\nدائماً في الخدمة والطاعة 🤍",
    "جزاك الله خير": "وإياك أجمعين يا رب 🤲\nبارك الله فيك ونفع بك 🌹",
    "ما هو التقويم الهجري": "التقويم الهجري هو التقويم الإسلامي الذي يبدأ من هجرة النبي ﷺ من مكة إلى المدينة 🌙\nيتكون من 12 شهراً قمرياً، وهو مرجع المسلمين للمناسبات الدينية 📅",
    "من انت": "أنا بوت التقويم الهجري 🤖\nمطور من قبل أبو سيف بن ذي يزن لخدمتك في الأمور الإسلامية 🌙",
}
AUTO_REPLIES.update(bot_data.get("auto_replies", {}))

DAILY_REMINDERS = [
    "🌅 سبحان الله وبحمده، سبحان الله العظيم 🌙",
    "🤲 اللهم أعني على ذكرك وشكرك وحسن عبادتك ✨",
    "💎 لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير 🌟",
    "🌸 أستغفر الله العظيم الذي لا إله إلا هو الحي القيوم وأتوب إليه 🤍",
    "📖 {وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا} - الطلاق 🌙",
]
DAILY_REMINDERS.extend(bot_data.get("daily_reminders", []))

CHANNEL_MESSAGES = [
    "🌙 بسم الله نبدأ يوماً جديداً\n\n💎 قال تعالى: {وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا}\n\n✨ اتق الله في السر والعلن...",
    "🌟 تذكير إيماني\n\n📖 قال رسول الله ﷺ: (إن الله جميل يحب الجمال)...",
]
CHANNEL_MESSAGES.extend(bot_data.get("channel_messages", []))

BANNED_USERS = set(bot_data.get("banned_users", []))

# --- In-memory state (not saved to DB, resets on restart) ---
user_messages = {}
user_threads = {}
user_message_count = {}
silenced_users = {}

# --- Anti-Spam and Ban System ---
def is_banned(user_id):
    return user_id in BANNED_USERS

def check_spam_limit(user_id):
    current_time = datetime.datetime.now()
    if user_id in silenced_users:
        silence_time = silenced_users[user_id]
        if (current_time - silence_time).total_seconds() < 30:
            return False, "silenced"
        else:
            del silenced_users[user_id]
            user_message_count[user_id] = {"count": 0, "last_reset": current_time}
    if user_id not in user_message_count:
        user_message_count[user_id] = {"count": 0, "last_reset": current_time}
    user_data = user_message_count[user_id]
    if (current_time - user_data["last_reset"]).total_seconds() > 60:
        user_data["count"] = 0
        user_data["last_reset"] = current_time
    user_data["count"] += 1
    if user_data["count"] > 5:
        silenced_users[user_id] = current_time
        user_data["count"] = 0
        return False, "limit_exceeded"
    return True, "allowed"

def get_spam_warning_message(status, user_name=""):
    if status == "limit_exceeded":
        return (f"⚠️ عذراً {user_name}!\n\n🚫 لقد تجاوزت الحد المسموح من الرسائل.\n⏰ تم إيقافك مؤقتاً لمدة 30 ثانية.")
    elif status == "silenced":
        return "🔇 أنت موقوف مؤقتاً. يرجى الانتظار قليلاً."
    return ""

# --- Keyboard Creation Functions ---
def create_admin_panel():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📝 إدارة الردود", callback_data="admin_replies"),
        InlineKeyboardButton("💭 إدارة التذكيرات", callback_data="admin_reminders"),
        InlineKeyboardButton("📢 رسائل القناة", callback_data="admin_channel"),
        InlineKeyboardButton("🚫 إدارة الحظر", callback_data="admin_ban"),
        InlineKeyboardButton("📤 النشر للجميع", callback_data="admin_broadcast"),
        InlineKeyboardButton("📊 إحصائيات البوت", callback_data="admin_stats"),
        InlineKeyboardButton("⚙️ إعدادات القناة", callback_data="admin_channel_settings"),
        InlineKeyboardButton("💬 إعدادات الرسائل", callback_data="admin_messages_settings"),
        InlineKeyboardButton("🔒 إدارة الوسائط", callback_data="admin_media_settings"),
        InlineKeyboardButton("🧠 إدارة الذاكرة", callback_data="admin_memory_management"),
        InlineKeyboardButton("🚀 نشر للإنتاج", callback_data="deploy_to_production"),
        InlineKeyboardButton("❌ إغلاق اللوحة", callback_data="close_panel")
    )
    return keyboard

def create_buttons():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("اليوم هجري", callback_data="hijri_today"))
    keyboard.add(InlineKeyboardButton("🕐 الساعة والتاريخ", callback_data="live_time"))
    keyboard.add(InlineKeyboardButton("تذكير يومي", callback_data="daily_reminder"))
    keyboard.add(InlineKeyboardButton("من المطور", callback_data="from_developer"))
    return keyboard

# --- Content Generation Functions ---
def get_hijri_date():
    if not convert:
        return "🌙 مكتبة `hijri-converter` غير مثبتة."
    try:
        today = datetime.date.today()
        hijri_date = convert.Gregorian(today.year, today.month, today.day).to_hijri()
        hijri_months = {1: "محرم", 2: "صفر", 3: "ربيع الأول", 4: "ربيع الآخر", 5: "جمادى الأولى", 6: "جمادى الآخرة", 7: "رجب", 8: "شعبان", 9: "رمضان", 10: "شوال", 11: "ذو القعدة", 12: "ذو الحجة"}
        weekdays = {0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"}
        weekday = weekdays[today.weekday()]
        hijri_month = hijri_months[hijri_date.month]
        return (f"🌙 التاريخ الهجري اليوم:\n📅 {hijri_date.day} {hijri_month} {hijri_date.year} هـ\n"
                f"📆 {weekday}\n\n📅 التاريخ الميلادي:\n🗓️ {today.strftime('%d/%m/%Y')} م")
    except Exception as e:
        return f"🌙 عذراً، حدث خطأ في جلب التاريخ: {e}"

def get_daily_reminder():
    return random.choice(DAILY_REMINDERS) if DAILY_REMINDERS else "لا توجد تذكيرات متاحة."

def get_live_time():
    if not pytz:
        return "🕐 مكتبة `pytz` غير مثبتة."
    try:
        riyadh_tz = pytz.timezone('Asia/Riyadh')
        now = datetime.datetime.now(riyadh_tz)
        weekdays = {0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"}
        months = {1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"}
        weekday = weekdays[now.weekday()]
        month = months[now.month]
        return (f"🕐 الساعة الآن: {now.strftime('%H:%M:%S')}\n"
                f"📅 التاريخ: {weekday} - {now.day} {month} {now.year}\n"
                f"🕌 بتوقيت مدينة الرياض - السعودية")
    except Exception as e:
        return f"🕐 عذراً، حدث خطأ في جلب الوقت: {e}"

async def handle_user_content(message, content_text=""):
    """Forwards user messages and media to the admin."""
    user_id = message.from_user.id
    username = message.from_user.username or "غير معروف"
    first_name = message.from_user.first_name or "غير معروف"

    if user_id not in USERS_LIST:
        USERS_LIST.add(user_id)
        bot_data["users"] = list(USERS_LIST)
        save_data(bot_data)

    admin_text = f"📩 رسالة جديدة من @{username} ({first_name}) - ID: {user_id}\n\n{content_text}"

    try:
        admin_msg = await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text)
        
        if message.content_type != 'text':
            try:
                await message.forward(ADMIN_CHAT_ID)
            except Exception as e:
                print(f"Error forwarding media: {e}")

        user_messages[admin_msg.message_id] = {
            "user_id": user_id, "user_message_id": message.message_id, "user_text": content_text
        }
        user_threads[user_id] = {
            "admin_message_id": admin_msg.message_id, "user_message_id": message.message_id
        }
    except Exception as e:
        print(f"Error sending message to admin: {e}")


