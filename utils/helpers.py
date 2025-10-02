import datetime
import random
import pytz
from hijri_converter import convert
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types

from database import load_data, save_data
from loader import bot
from config import ADMIN_CHAT_ID

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
        InlineKeyboardButton(text="🧠 إدارة الذاكرة", callback_data="admin_memory_management"),
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

def get_hijri_date():
    try:
        today = datetime.date.today()
        hijri_date = convert.Gregorian(today.year, today.month, today.day).to_hijri()
        hijri_months = {
            1: "محرم", 2: "صفر", 3: "ربيع الأول", 4: "ربيع الآخر", 5: "جمادى الأولى",
            6: "جمادى الآخرة", 7: "رجب", 8: "شعبان", 9: "رمضان", 10: "شوال",
            11: "ذو القعدة", 12: "ذو الحجة"
        }
        weekdays = {
            0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس",
            4: "الجمعة", 5: "السبت", 6: "الأحد"
        }
        weekday = weekdays[today.weekday()]
        hijri_month = hijri_months[hijri_date.month]
        result = (
            f"**التاريخ الهجري:** {hijri_date.day} {hijri_month} {hijri_date.year} هـ\n"
            f"**اليوم:** {weekday}\n\n"
            f"**التاريخ الميلادي:** {today.strftime('%d/%m/%Y')} م"
        )
        return result
    except Exception as e:
        return f"🌙 عذراً، حدث خطأ في جلب التاريخ: {e}"

def get_live_time():
    try:
        riyadh_tz = pytz.timezone('Asia/Riyadh')
        now = datetime.datetime.now(riyadh_tz)
        weekdays = {
            0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس",
            4: "الجمعة", 5: "السبت", 6: "الأحد"
        }
        time_text = (
            f"**التوقيت الحالي (الرياض):**\n"
            f"🕐 **الساعة:** {now.strftime('%H:%M:%S')}\n"
            f"📅 **التاريخ:** {weekdays[now.weekday()]}، {now.strftime('%d/%m/%Y')}"
        )
        return time_text
    except Exception as e:
        return f"🕐 عذراً، حدث خطأ في جلب الوقت: {e}"

def get_daily_reminder():
    if not DAILY_REMINDERS:
        return "لا توجد تذكيرات متاحة حالياً."
    return random.choice(DAILY_REMINDERS)

async def handle_user_content(message: types.Message):
    """
    تعيد توجيه رسالة المستخدم إلى المشرف وتسجل بيانات المحادثة.
    """
    user_id = message.from_user.id
    try:
        forwarded_message = await message.forward(ADMIN_CHAT_ID)
        # تسجيل بيانات المحادثة للرد عليها لاحقاً
        user_threads[user_id] = message.message_id
    except Exception as e:
        print(f"فشل إعادة توجيه الرسالة من {user_id}: {e}")
