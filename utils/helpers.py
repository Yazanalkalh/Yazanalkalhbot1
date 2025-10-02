import datetime
import random
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import load_data, save_data
import config  # استيراد ملف الإعدادات للوصول للمتغيرات

# --- تحميل البيانات والمتغيرات العامة ---
bot_data = load_data()

# هذه القوائم سيتم تحديثها تلقائياً من البيانات المحملة
USERS_LIST = set(bot_data.get("users", []))
AUTO_REPLIES = bot_data.get("auto_replies", {})
DAILY_REMINDERS = bot_data.get("daily_reminders", [])
CHANNEL_MESSAGES = bot_data.get("channel_messages", [])
BANNED_USERS = set(bot_data.get("banned_users", []))

# متغيرات للذاكرة المؤقتة (Anti-Spam والمحادثات)
user_messages = {}
user_threads = {}
user_message_count = {}
silenced_users = {}
start_time = datetime.datetime.now()

# --- دوال مساعدة أساسية ---

def is_banned(user_id):
    """التحقق مما إذا كان المستخدم محظوراً."""
    return user_id in BANNED_USERS

def check_spam_limit(user_id):
    """التحقق من تجاوز حد الرسائل المزعجة."""
    current_time = datetime.datetime.now()
    if user_id in silenced_users and (current_time - silenced_users[user_id]).total_seconds() < 30:
        return False, "silenced"
    
    user_data = user_message_count.setdefault(user_id, {"count": 0, "last_reset": current_time})
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
    """إنشاء رسالة تحذير للمستخدم المزعج."""
    if status == "limit_exceeded":
        return f"⚠️ عذراً {user_name}، لقد تجاوزت حد الرسائل المسموح. تم إيقافك مؤقتاً لمدة 30 ثانية."
    elif status == "silenced":
        return "🔇 أنت موقوف مؤقتاً. يرجى الانتظار قليلاً."
    return ""

async def handle_user_content(message, content_text=""):
    """
    الدالة المركزية لإعادة توجيه رسائل المستخدمين للمشرف.
    -- تم التحديث هنا لحل مشكلة إعادة التوجيه --
    """
    user_id = message.from_user.id
    username = message.from_user.username or "غير معروف"
    first_name = message.from_user.first_name or "غير معروف"

    # إضافة المستخدم الجديد إذا لم يكن موجوداً
    if user_id not in USERS_LIST:
        USERS_LIST.add(user_id)
        bot_data["users"] = list(USERS_LIST)
        save_data(bot_data)

    # 1. إرسال رسالة إشعار للمشرف (اختياري لكن مفيد)
    admin_text = f"📩 رسالة جديدة من: {first_name} (@{username})\nID: `{user_id}`"
    try:
        admin_msg = await config.bot.send_message(chat_id=config.ADMIN_CHAT_ID, text=admin_text, parse_mode="Markdown")
        
        # 2. **إعادة توجيه الرسالة الأصلية بالكامل للمشرف**
        # هذا هو التصحيح الرئيسي لمشكلة (text)
        forwarded_msg = await message.forward(config.ADMIN_CHAT_ID)

        # حفظ معلومات الرسالة للرد عليها لاحقاً
        # سنستخدم ID الرسالة المعاد توجيهها
        user_messages[forwarded_msg.message_id] = {
            "user_id": user_id,
            "user_message_id": message.message_id,
            "user_text": content_text
        }
    except Exception as e:
        print(f"❌ خطأ في إرسال رسالة للمشرف: {e}")

# --- دوال إنشاء الأزرار ---

def create_admin_panel():
    """إنشاء لوحة التحكم الرئيسية للمشرف."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        ("📝 إدارة الردود", "admin_replies"), ("💭 إدارة التذكيرات", "admin_reminders"),
        ("📢 رسائل القناة", "admin_channel"), ("🚫 إدارة الحظر", "admin_ban"),
        ("📤 النشر للجميع", "admin_broadcast"), ("📊 إحصائيات البوت", "admin_stats"),
        ("⚙️ إعدادات القناة", "admin_channel_settings"), ("💬 إعدادات الرسائل", "admin_messages_settings"),
        ("🔒 إدارة الوسائط", "admin_media_settings"), ("🧠 إدارة الذاكرة", "admin_memory_management"),
        ("🚀 حالة الإنتاج", "deploy_to_production"), ("❌ إغلاق اللوحة", "close_panel")
    ]
    keyboard.add(*(InlineKeyboardButton(text, callback_data=data) for text, data in buttons))
    return keyboard

def create_buttons():
    """إنشاء الأزرار الرئيسية للمستخدم."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        ("اليوم هجري", "hijri_today"), ("🕐 الساعة والتاريخ", "live_time"),
        ("تذكير يومي", "daily_reminder"), ("من المطور", "from_developer")
    ]
    keyboard.add(*(InlineKeyboardButton(text, callback_data=data) for text, data in buttons))
    return keyboard

# --- دوال جلب المعلومات ---

def get_hijri_date():
    """جلب التاريخ الهجري والميلادي."""
    # (الكود لم يتغير)
    try:
        from hijri_converter import convert
        today = datetime.date.today()
        hijri_date = convert.Gregorian(today.year, today.month, today.day).to_hijri()
        hijri_months = {1: "محرم", 2: "صفر", 3: "ربيع الأول", 4: "ربيع الآخر", 5: "جمادى الأولى", 6: "جمادى الآخرة", 7: "رجب", 8: "شعبان", 9: "رمضان", 10: "شوال", 11: "ذو القعدة", 12: "ذو الحجة"}
        weekdays = {0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"}
        weekday = weekdays[today.weekday()]
        hijri_month = hijri_months[hijri_date.month]
        return (f"🌙 **التاريخ الهجري:** {hijri_date.day} {hijri_month} {hijri_date.year} هـ\n"
                f"📆 **اليوم:** {weekday}\n\n"
                f"📅 **التاريخ الميلادي:** {today.strftime('%d/%m/%Y')} م")
    except Exception:
        return "عذراً، حدث خطأ في جلب التاريخ الهجري."

def get_live_time():
    """جلب الوقت والتاريخ الحالي."""
    # (الكود لم يتغير)
    try:
        import pytz
        now = datetime.datetime.now(pytz.timezone('Asia/Riyadh'))
        weekdays = {0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"}
        months = {1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"}
        return (f"🕐 **الساعة الآن:** {now.strftime('%H:%M:%S')}\n"
                f"📅 **التاريخ:** {weekdays[now.weekday()]} - {now.day} {months[now.month]} {now.year}\n"
                f"🕌 بتوقيت الرياض")
    except Exception:
        return "عذراً، حدث خطأ في جلب الوقت."

def get_daily_reminder():
    """الحصول على تذكير يومي عشوائي."""
    return random.choice(DAILY_REMINDERS) if DAILY_REMINDERS else "لا توجد تذكيرات متاحة حالياً."


 
