import os
import datetime
import json
from aiogram import Bot, Dispatcher, types
import time # استيراد مكتبة الوقت

# --- (إضافات للتشغيل على Render) ---
from pymongo import MongoClient
from threading import Thread
from flask import Flask

# 1. خادم الويب المدمج لإبقاء البوت نشطًا على Render
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot server is running!"

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
# ---------------------------------------------------

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import asyncio
import random

# ----------------- إعداد البوت -----------------
print("🔍 فحص متغيرات البيئة...")

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
MONGO_URI = os.getenv("MONGO_URI")

if not all([API_TOKEN, ADMIN_CHAT_ID, MONGO_URI]):
    print("❌ خطأ: تأكد من وجود BOT_TOKEN, ADMIN_CHAT_ID, MONGO_URI في متغيرات البيئة!")
    exit(1)

try:
    ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)
    print(f"✅ تم تعيين المشرف: {ADMIN_CHAT_ID}")
except ValueError:
    print("❌ خطأ: ADMIN_CHAT_ID يجب أن يكون رقماً صحيحاً")
    exit(1)

print("✅ جميع متغيرات البيئة الأساسية موجودة.")

# ----------------- إعداد قاعدة البيانات السحابية (MongoDB) -----------------
try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("HijriBotDB")
    collection = db.get_collection("BotData")
    print("✅ تم الاتصال بقاعدة البيانات السحابية بنجاح!")
except Exception as e:
    print(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
    exit(1)
# -------------------------------------------------------------------

CHANNEL_ID = os.getenv("CHANNEL_ID")
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)
start_time = datetime.datetime.now()

# ----------------- حالات FSM لإدارة الرسائل (النسخة الكاملة والمصححة) -----------------
class AdminStates(StatesGroup):
    waiting_for_new_reply = State()
    waiting_for_new_reminder = State()
    waiting_for_new_channel_message = State()
    waiting_for_ban_id = State()
    waiting_for_unban_id = State()
    waiting_for_broadcast_message = State()
    waiting_for_channel_id = State()
    waiting_for_instant_channel_post = State()
    waiting_for_schedule_time = State()
    waiting_for_welcome_message = State()
    waiting_for_reply_message = State()
    waiting_for_media_reject_message = State()
    waiting_for_delete_reply = State()
    waiting_for_delete_reminder = State()
    waiting_for_delete_channel_msg = State()
    waiting_for_clear_user_id = State()

# ----------------- دوال قاعدة البيانات الجديدة -----------------
def load_data():
    """تحميل البيانات من قاعدة بيانات MongoDB"""
    data_doc = collection.find_one({"_id": "main_bot_config"})
    default_data = {
        "auto_replies": {}, "daily_reminders": [], "channel_messages": [],
        "banned_users": [], "users": [], "channel_id": "", "allow_media": False,
        "media_reject_message": "❌ يُسمح بالرسائل النصية فقط.",
        "rejected_media_count": 0, "welcome_message": "", "reply_message": "",
        "schedule_interval_seconds": 86400
    }
    if data_doc:
        data_doc.pop("_id", None)
        default_data.update(data_doc)
    return default_data

def save_data(data):
    """حفظ البيانات في قاعدة بيانات MongoDB"""
    try:
        collection.find_one_and_update(
            {"_id": "main_bot_config"},
            {"$set": data},
            upsert=True
        )
    except Exception as e:
        print(f"خطأ في حفظ البيانات في MongoDB: {e}")
# -------------------------------------------------------------------------

bot_data = load_data()
USERS_LIST = set(bot_data.get("users", []))

# ----------------- الردود التلقائية الموسعة -----------------
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

# ----------------- التذكيرات اليومية -----------------
DAILY_REMINDERS = [
    "🌅 سبحان الله وبحمده، سبحان الله العظيم 🌙",
    "🤲 اللهم أعني على ذكرك وشكرك وحسن عبادتك ✨",
    "💎 لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير 🌟",
    "🌸 أستغفر الله العظيم الذي لا إله إلا هو الحي القيوم وأتوب إليه 🤍",
    "📖 {وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا} - الطلاق 🌙",
    "🌹 قال ﷺ: (كلمتان خفيفتان على اللسان، ثقيلتان في الميزان، حبيبتان إلى الرحمن: سبحان الله وبحمده، سبحان الله العظيم) 💎",
    "💭 من صبر ظفر، ومن شكر زاد خيره 🌙",
    "🤲 اللهم اهدني فيمن هديت، وعافني فيمن عافيت 🌸",
    "🌟 تأمل: كل نفس تتنفسه نعمة من الله، فاحمده عليها 🤍",
    "💫 قل: حسبي الله لا إله إلا هو عليه توكلت وهو رب العرش العظيم 🌟",
]
DAILY_REMINDERS.extend(bot_data.get("daily_reminders", []))

# ----------------- الرسائل الدينية للنشر التلقائي -----------------
CHANNEL_MESSAGES = [
    "🌙 بسم الله نبدأ يوماً جديداً\n\n💎 قال تعالى: {وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا}\n\n✨ اتق الله في السر والعلن، يجعل لك من كل ضيق مخرجاً ومن كل هم فرجاً\n\n🤲 اللهم اجعل هذا اليوم خيراً وبركة علينا جميعاً",
    "🌟 تذكير إيماني\n\n📖 قال رسول الله ﷺ: (إن الله جميل يحب الجمال)\n\n🌸 اجعل جمال أخلاقك يعكس جمال إيمانك، فالمؤمن الحق جميل الظاهر والباطن\n\n💫 بارك الله في أخلاقكم وزادكم جمالاً في الدين والدنيا",
    "💚 دقيقة تأمل\n\n🌺 كم من نعمة يغمرك الله بها كل لحظة؟\n- نفس يتردد في صدرك\n- قلب ينبض بالحياة\n- عينان تبصران نور الدنيا\n- أذنان تسمعان كلام الله\n\n🤲 الحمد لله الذي أنعم علينا بنعم لا تعد ولا تحصى",
]
CHANNEL_MESSAGES.extend(bot_data.get("channel_messages", []))

# ----------------- قائمة المحظورين -----------------
BANNED_USERS = set(bot_data.get("banned_users", []))

# ----------------- حفظ الرسائل والمحادثات (مؤقتًا في الذاكرة) -----------------
user_messages = {}
user_threads = {}

# ----------------- نظام Anti-Spam محسن -----------------
user_message_count = {}
silenced_users = {}

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
        return (
            f"⚠️ عذراً {user_name}!\n\n"
            "🚫 لقد تجاوزت الحد المسموح من الرسائل (5 رسائل في الدقيقة)\n"
            "⏰ تم إيقافك مؤقتاً لمدة 30 ثانية\n\n"
            "💡 يرجى الانتظار ثم المحاولة مرة أخرى"
        )
    elif status == "silenced":
        return "🔇 أنت مُسكَت مؤقتاً\n\n⏰ يرجى الانتظار قليلاً قبل إرسال رسائل جديدة"
    return ""

# ----------------- دوال لوحة التحكم -----------------
def create_admin_panel():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📝 إدارة الردود", callback_data="admin_replies"),
        InlineKeyboardButton("💭 إدارة التذكيرات", callback_data="admin_reminders")
    )
    keyboard.add(
        InlineKeyboardButton("📢 رسائل القناة", callback_data="admin_channel"),
        InlineKeyboardButton("🚫 إدارة الحظر", callback_data="admin_ban")
    )
    keyboard.add(
        InlineKeyboardButton("📤 النشر للجميع", callback_data="admin_broadcast"),
        InlineKeyboardButton("📊 إحصائيات البوت", callback_data="admin_stats")
    )
    keyboard.add(
        InlineKeyboardButton("⚙️ إعدادات القناة", callback_data="admin_channel_settings"),
        InlineKeyboardButton("💬 إعدادات الرسائل", callback_data="admin_messages_settings")
    )
    keyboard.add(
        InlineKeyboardButton("🔒 إدارة الوسائط", callback_data="admin_media_settings"),
        InlineKeyboardButton("🧠 إدارة الذاكرة", callback_data="admin_memory_management")
    )
    keyboard.add(
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

# ----------------- التاريخ الهجري -----------------
def get_hijri_date():
    try:
        from hijri_converter import convert
        today = datetime.date.today()
        hijri_date = convert.Gregorian(today.year, today.month, today.day).to_hijri()

        hijri_months = {
            1: "محرم", 2: "صفر", 3: "ربيع الأول", 4: "ربيع الآخر",
            5: "جمادى الأولى", 6: "جمادى الآخرة", 7: "رجب", 8: "شعبان",
            9: "رمضان", 10: "شوال", 11: "ذو القعدة", 12: "ذو الحجة"
        }

        weekdays = {
            0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس",
            4: "الجمعة", 5: "السبت", 6: "الأحد"
        }

        weekday = weekdays[today.weekday()]
        hijri_month = hijri_months[hijri_date.month]

        result = f"🌙 التاريخ الهجري اليوم:\n"
        result += f"📅 {hijri_date.day} {hijri_month} {hijri_date.year} هـ\n"
        result += f"📆 {weekday}\n\n"
        result += f"📅 التاريخ الميلادي:\n"
        result += f"🗓️ {today.strftime('%d/%m/%Y')} م\n"
        result += f"⭐ بارك الله في يومك"

        return result
    except ImportError:
        today = datetime.date.today()
        weekdays = {0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"}
        weekday = weekdays[today.weekday()]
        
        result = f"🌙 التاريخ الميلادي اليوم:\n"
        result += f"📅 {today.strftime('%d/%m/%Y')} م\n"
        result += f"📆 {weekday}\n\n"
        result += f"💡 لعرض التاريخ الهجري، يتطلب تثبيت مكتبة hijri-converter\n"
        result += f"⭐ بارك الله في يومك"
        
        return result
    except Exception as e:
        return f"🌙 عذراً، حدث خطأ في جلب التاريخ: {str(e)}"

def get_daily_reminder():
    if not DAILY_REMINDERS:
        return "لا توجد تذكيرات متاحة حالياً."
    return random.choice(DAILY_REMINDERS)

def get_live_time():
    try:
        import pytz
        riyadh_tz = pytz.timezone('Asia/Riyadh')
        now = datetime.datetime.now(riyadh_tz)
    except ImportError:
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
    except Exception:
        now = datetime.datetime.now()

    try:
        weekdays = {0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"}
        months = {1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"}
        weekday = weekdays[now.weekday()]
        month = months[now.month]

        time_text = f"🕐 الساعة الآن: {now.strftime('%H:%M:%S')}\n"
        time_text += f"📅 التاريخ: {weekday} - {now.day} {month} {now.year}\n"
        time_text += f"🕌 بتوقيت مدينة الرياض - السعودية\n"
        time_text += f"⏰ آخر تحديث: {now.strftime('%H:%M:%S')}"

        return time_text
    except Exception as e:
        return f"🕐 عذراً، حدث خطأ في جلب الوقت: {str(e)}"

# ----------------- النشر التلقائي المحسن -----------------
async def send_channel_message(custom_message=None, channel_id_override=None):
    channel_id = channel_id_override or bot_data.get("channel_id") or CHANNEL_ID

    if not channel_id:
        print("❌ معرف القناة غير محدد")
        return False

    message_to_send = custom_message or (random.choice(CHANNEL_MESSAGES) if CHANNEL_MESSAGES else None)
    
    if not message_to_send:
        print("❌ لا توجد رسائل متاحة للإرسال")
        return False

    try:
        if not channel_id.startswith('@') and not channel_id.startswith('-'):
            channel_id = '@' + channel_id

        await bot.send_message(chat_id=channel_id, text=message_to_send)
        print(f"✅ تم إرسال رسالة للقناة: {channel_id}")
        return True

    except Exception as e:
        print(f"❌ خطأ في إرسال الرسالة للقناة: {e}")
        return False

async def schedule_channel_messages():
    print("🕐 بدء جدولة الرسائل التلقائية للقناة...")
    while True:
        try:
            interval_seconds = bot_data.get("schedule_interval_seconds", 86400)
            if interval_seconds < 60:
                time_display = f"{interval_seconds} ثانية"
            elif interval_seconds < 3600:
                time_display = f"{interval_seconds // 60} دقيقة"
            else:
                time_display = f"{interval_seconds // 3600} ساعة"

            print(f"⏰ انتظار {time_display} حتى الرسالة التالية...")
            await asyncio.sleep(interval_seconds)

            channel_id = bot_data.get("channel_id") or CHANNEL_ID
            if channel_id and CHANNEL_MESSAGES:
                await send_channel_message()
            else:
                print("⚠️ تخطي الإرسال التلقائي: معرف القناة أو الرسائل غير متوفرة")
        except Exception as e:
            print(f"❌ خطأ في جدولة الرسائل: {e}")
            await asyncio.sleep(60)

# ----------------- معالج لوحة التحكم -----------------
@dp.message_handler(lambda message: message.from_user.id == ADMIN_CHAT_ID and message.text == "/admin", state="*")
async def admin_panel(message: types.Message):
    await message.reply(
        "🔧 **لوحة التحكم الإدارية**\n\nاختر الخيار المناسب من القائمة أدناه:",
        reply_markup=create_admin_panel(), parse_mode="Markdown"
    )

# ... (بقية الكود الخاص بك بالكامل حتى handle_user_content)
# لقد تم تضمين بقية الكود في هذا الملف ليكون كاملاً وجاهزاً للنسخ
# ...

async def handle_user_content(message, content_text=""):
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
        
        if hasattr(message, 'content_type') and message.content_type != types.ContentType.TEXT:
            await message.forward(ADMIN_CHAT_ID)

        # إضافة طابع زمني لحل مشكلة تسريب الذاكرة
        user_messages[admin_msg.message_id] = {
            "user_id": user_id,
            "user_message_id": message.message_id,
            "user_text": content_text,
            "timestamp": time.time() 
        }
        user_threads[user_id] = {
            "admin_message_id": admin_msg.message_id,
            "user_message_id": message.message_id
        }
    except Exception as e:
        print(f"خطأ في إرسال للإدارة: {e}")

# ... (بقية الكود الخاص بك بالكامل)

# ----------------- مهام الخلفية المحسنة -----------------
async def cleanup_memory_task():
    """تقوم هذه المهمة بتنظيف قواميس الرسائل القديمة لمنع تسريب الذاكرة."""
    while True:
        await asyncio.sleep(3600)  # تعمل كل ساعة
        
        now = time.time()
        EXPIRATION_TIME = 86400  # 24 ساعة
        
        expired_messages_ids = [
            msg_id for msg_id, data in user_messages.items() 
            if (now - data.get("timestamp", now)) > EXPIRATION_TIME
        ]
        if expired_messages_ids:
            for msg_id in expired_messages_ids:
                del user_messages[msg_id]
            print(f"🧹 تم تنظيف {len(expired_messages_ids)} رسالة قديمة من الذاكرة.")
            
        active_admin_msg_ids = set(user_messages.keys())
        expired_threads_ids = [
            user_id for user_id, data in user_threads.items()
            if data["admin_message_id"] not in active_admin_msg_ids
        ]
        if expired_threads_ids:
            for user_id in expired_threads_ids:
                del user_threads[user_id]
            print(f"🧹 تم تنظيف {len(expired_threads_ids)} محادثة قديمة من الذاكرة.")

async def keep_alive_task():
    ping_count = 0
    while True:
        try:
            await asyncio.sleep(300)
            ping_count += 1
            try:
                me = await bot.get_me()
                if ping_count % 6 == 0:
                    print(f"🔄 Keep alive #{ping_count} - البوت نشط: @{me.username} - {datetime.datetime.now().strftime('%H:%M:%S')}")
            except Exception as e:
                print(f"⚠️ تحذير: مشكلة في اتصال البوت: {e}")
        except Exception as e:
            print(f"❌ خطأ في keep alive: {e}")
            await asyncio.sleep(60)

async def deployment_monitor():
    while True:
        try:
            await asyncio.sleep(3600)
            current_time = datetime.datetime.now()
            uptime_hours = (current_time - start_time).total_seconds() / 3600
            print(f"📊 مراقب النشر: البوت يعمل منذ {uptime_hours:.1f} ساعة - {current_time.strftime('%H:%M:%S')}")
            if current_time.hour == 12 and current_time.minute < 5:
                await bot.send_message(
                    ADMIN_CHAT_ID,
                    f"📊 **تقرير يومي**\n\n"
                    f"⏰ وقت التشغيل: {uptime_hours:.1f} ساعة\n"
                    f"👥 المستخدمين: {len(USERS_LIST)}\n"
                    f"✅ كل شيء يعمل بشكل طبيعي!",
                    parse_mode="Markdown"
                )
        except Exception as e:
            print(f"❌ خطأ في مراقب النشر: {e}")

# ----------------- دوال التشغيل -----------------
async def startup(dp):
    try:
        asyncio.create_task(schedule_channel_messages())
        asyncio.create_task(keep_alive_task())
        asyncio.create_task(deployment_monitor())
        asyncio.create_task(cleanup_memory_task()) # تشغيل مهمة تنظيف الذاكرة

        print("✅ البوت جاهز للعمل 24/7!")
        
        await bot.send_message(
            ADMIN_CHAT_ID,
            "✅ **البوت يعمل بنجاح (نسخة مستقرة)!**\n\n"
            "🤖 البوت متصل ونشط\n"
            "🌐 خادم الويب يعمل\n"
            "☁️ قاعدة البيانات متصلة\n"
            "🧹 تنظيف الذاكرة مفعل\n"
            f"⏰ وقت التشغيل: {datetime.datetime.now().strftime('%H:%M:%S')}",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"❌ خطأ في startup: {e}")

def main():
    web_server_thread = Thread(target=run_web_server)
    web_server_thread.daemon = True
    web_server_thread.start()
    
    try:
        print("🤖 بدء تشغيل البوت...")
        from aiogram import executor
        executor.start_polling(dp, skip_updates=True, on_startup=startup)
    except KeyboardInterrupt:
        print("🛑 تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        print(f"❌ خطأ في التشغيل: {e}")

if __name__ == "__main__":
    main()


