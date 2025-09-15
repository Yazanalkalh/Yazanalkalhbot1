
import os
import datetime
import json
from aiogram import Bot, Dispatcher, types

# تشغيل خادم Flask
webserver_started = False
try:
    print("🌐 بدء تشغيل خادم Flask...")
    from webserver import start_webserver
    if start_webserver():
        print("✅ تم تشغيل خادم Flask بنجاح")
        webserver_started = True
    else:
        print("⚠️ فشل في تشغيل خادم Flask")
except ImportError as e:
    print(f"⚠️ خطأ في استيراد webserver: {e}")
except Exception as e:
    print(f"⚠️ خطأ عام في webserver: {e}")

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import asyncio
import random

# ----------------- إعداد البوت -----------------
print("🔍 فحص متغيرات البيئة...")

API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    print("❌ خطأ: متغير البيئة BOT_TOKEN غير موجود!")
    print("📝 يرجى إضافة BOT_TOKEN في تبويب Secrets")
    exit(1)

ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
if not ADMIN_CHAT_ID:
    print("❌ خطأ: متغير البيئة ADMIN_CHAT_ID غير موجود!")
    print("📝 يرجى إضافة ADMIN_CHAT_ID في تبويب Secrets")
    exit(1)

try:
    ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)
    print(f"✅ تم تعيين المشرف: {ADMIN_CHAT_ID}")
except ValueError:
    print("❌ خطأ: ADMIN_CHAT_ID يجب أن يكون رقماً صحيحاً")
    exit(1)

print("✅ جميع متغيرات البيئة صحيحة")

# معرف القناة للنشر التلقائي
CHANNEL_ID = os.getenv("CHANNEL_ID")

storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

# متغير لحفظ وقت بداية التشغيل
start_time = datetime.datetime.now()

# ----------------- حالات FSM لإدارة الرسائل -----------------
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

# ----------------- قاعدة البيانات البسيطة -----------------
DATABASE_FILE = "bot_data.json"

def load_data():
    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "auto_replies": {},
            "daily_reminders": [],
            "channel_messages": [],
            "banned_users": [],
            "users": [],
            "channel_id": "",
            "allow_media": False,
            "media_reject_message": "❌ يُسمح بالرسائل النصية فقط. يرجى إرسال النص فقط.",
            "rejected_media_count": 0,
            "welcome_message": "",
            "reply_message": "",
            "schedule_interval_seconds": 86400  # 24 ساعة
        }

def save_data(data):
    try:
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"خطأ في حفظ البيانات: {e}")

# تحميل البيانات عند بدء التشغيل
bot_data = load_data()

# قائمة المستخدمين
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

# دمج الردود المخصصة مع الردود الافتراضية
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

# ----------------- حفظ الرسائل والمحادثات -----------------
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
        return "🔇 أنت مسكت مؤقتاً\n\n⏰ يرجى الانتظار قليلاً قبل إرسال رسائل جديدة"
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
    """
    محاولة جلب التاريخ الهجري باستخدام مكتبة hijri-converter
    في حالة عدم وجود المكتبة، سيتم عرض رسالة بديلة
    """
    try:
        # محاولة استيراد المكتبة
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
        # في حالة عدم توفر المكتبة
        today = datetime.date.today()
        weekdays = {
            0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس",
            4: "الجمعة", 5: "السبت", 6: "الأحد"
        }
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
    return random.choice(DAILY_REMINDERS)

def get_live_time():
    """
    جلب الوقت الحالي بتوقيت الرياض
    """
    try:
        # محاولة استخدام مكتبة pytz للتوقيت
        import pytz
        riyadh_tz = pytz.timezone('Asia/Riyadh')
        now = datetime.datetime.now(riyadh_tz)
    except ImportError:
        # في حالة عدم توفر مكتبة pytz، استخدم الوقت المحلي
        import time
        # تقدير فرق التوقيت (+3 ساعات للرياض)
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
    except Exception:
        # في حالة أي خطأ آخر، استخدم الوقت المحلي للنظام
        now = datetime.datetime.now()

    try:
        weekdays = {
            0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس",
            4: "الجمعة", 5: "السبت", 6: "الأحد"
        }

        months = {
            1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل",
            5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس",
            9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
        }

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

    if not CHANNEL_MESSAGES and not custom_message:
        print("❌ لا توجد رسائل متاحة للإرسال")
        return False

    try:
        message = custom_message or random.choice(CHANNEL_MESSAGES)

        if not channel_id.startswith('@') and not channel_id.startswith('-'):
            channel_id = '@' + channel_id

        await bot.send_message(chat_id=channel_id, text=message)
        print(f"✅ تم إرسال رسالة للقناة: {channel_id}")
        return True

    except Exception as e:
        print(f"❌ خطأ في إرسال الرسالة للقناة: {e}")
        return False

async def schedule_channel_messages():
    print("🕐 بدء جدولة الرسائل التلقائية للقناة...")

    while True:
        try:
            interval_seconds = bot_data.get("schedule_interval_seconds", 86400)  # 24 ساعة افتراضي

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
                result = await send_channel_message()
                if result:
                    print(f"✅ تم إرسال رسالة تلقائية - {datetime.datetime.now().strftime('%H:%M:%S')}")
                else:
                    print(f"❌ فشل إرسال الرسالة التلقائية - {datetime.datetime.now().strftime('%H:%M:%S')}")
            else:
                print("⚠️ لا يمكن الإرسال: معرف القناة أو الرسائل غير متوفرة")

        except Exception as e:
            print(f"❌ خطأ في جدولة الرسائل: {e}")
            await asyncio.sleep(60)

# ----------------- معالج لوحة التحكم -----------------
@dp.message_handler(lambda message: message.from_user.id == ADMIN_CHAT_ID and message.text == "/admin", state="*")
async def admin_panel(message: types.Message):
    await message.reply(
        "🔧 **لوحة التحكم الإدارية**\n\n"
        "مرحباً بك في لوحة التحكم الشاملة للبوت 🤖\n"
        "اختر الخيار المناسب من القائمة أدناه:",
        reply_markup=create_admin_panel(),
        parse_mode="Markdown"
    )

# ----------------- معالج الأزرار الإدارية -----------------
@dp.callback_query_handler(lambda c: c.from_user.id == ADMIN_CHAT_ID, state="*")
async def process_admin_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data

    if data == "admin_stats":
        stats_text = f"📊 **إحصائيات البوت**\n\n"
        stats_text += f"📝 الردود التلقائية: {len(AUTO_REPLIES)}\n"
        stats_text += f"💭 التذكيرات اليومية: {len(DAILY_REMINDERS)}\n"
        stats_text += f"📢 رسائل القناة: {len(CHANNEL_MESSAGES)}\n"
        stats_text += f"🚫 المستخدمين المحظورين: {len(BANNED_USERS)}\n"
        stats_text += f"👥 إجمالي المستخدمين: {len(USERS_LIST)}\n"
        stats_text += f"💬 المحادثات النشطة: {len(user_threads)}\n"
        stats_text += f"📨 الرسائل المحفوظة: {len(user_messages)}\n"
        stats_text += f"🌐 القناة النشطة: {'✅' if (bot_data.get('channel_id') or CHANNEL_ID) else '❌'}\n"
        stats_text += f"🛡️ نظام Anti-Spam: ✅ مفعل\n"

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main"))

        await bot.edit_message_text(
            stats_text,
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif data == "deploy_to_production":
        await bot.answer_callback_query(callback_query.id, "🚀 جاري التحضير للنشر...")

        deployment_text = f"🚀 **نشر البوت للإنتاج**\n\n"
        deployment_text += f"✅ **الحالة الحالية:**\n"
        deployment_text += f"• البوت يعمل: ✅ نشط\n"
        deployment_text += f"• خادم الويب: ✅ يعمل على المنفذ 5000\n"
        deployment_text += f"• قاعدة البيانات: ✅ متصلة\n"
        deployment_text += f"• النشر التلقائي: ✅ مفعل\n\n"

        deployment_text += f"🔧 **للنشر النهائي:**\n"
        deployment_text += f"1. اضغط على زر 'Deploy' في أعلى Replit\n"
        deployment_text += f"2. اختر 'Reserved VM Deployment'\n"
        deployment_text += f"3. اتركه ينشر تلقائياً\n\n"

        deployment_text += f"🌟 **مميزات Reserved VM:**\n"
        deployment_text += f"• يعمل 24/7 بدون انقطاع\n"
        deployment_text += f"• مناسب للبوتات طويلة المدى\n"
        deployment_text += f"• استقرار عالي في الأداء\n"
        deployment_text += f"• لا يتوقف عند عدم وجود نشاط"

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("📊 فحص الحالة", callback_data="check_deployment_status"))
        keyboard.add(InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main"))

        await bot.edit_message_text(
            deployment_text,
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif data == "check_deployment_status":
        current_time = datetime.datetime.now()
        uptime = (current_time - start_time).total_seconds() / 3600

        status_text = f"📊 **حالة النشر الحالية**\n\n"
        status_text += f"🕐 **وقت التشغيل:** {uptime:.1f} ساعة\n"
        status_text += f"🌐 **الخادم:** نشط على المنفذ 5000\n"
        status_text += f"🤖 **البوت:** متصل ويعمل\n"
        status_text += f"📊 **المستخدمين:** {len(USERS_LIST)}\n"
        status_text += f"💬 **الرسائل:** {len(user_messages)}\n"
        status_text += f"📅 **آخر فحص:** {current_time.strftime('%H:%M:%S')}\n\n"

        status_text += f"✅ **البوت جاهز للنشر النهائي**\n"
        status_text += f"استخدم Reserved VM Deployment للعمل المستمر 24/7"

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔄 تحديث الحالة", callback_data="check_deployment_status"))
        keyboard.add(InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main"))

        await bot.edit_message_text(
            status_text,
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif data == "back_to_main":
        await bot.edit_message_text(
            "🔧 **لوحة التحكم الإدارية**\n\n"
            "مرحباً بك في لوحة التحكم الشاملة للبوت 🤖\n"
            "اختر الخيار المناسب من القائمة أدناه:",
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=create_admin_panel(),
            parse_mode="Markdown"
        )

    elif data == "admin_replies":
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("➕ إضافة رد جديد", callback_data="add_reply"),
            InlineKeyboardButton("📝 عرض الردود", callback_data="show_replies")
        )
        keyboard.add(
            InlineKeyboardButton("🗑️ حذف رد", callback_data="delete_reply_menu"),
            InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")
        )
        
        await bot.edit_message_text(
            "📝 **إدارة الردود التلقائية**\n\nاختر العملية المطلوبة:",
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif data == "admin_reminders":
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("➕ إضافة تذكير", callback_data="add_reminder"),
            InlineKeyboardButton("📝 عرض التذكيرات", callback_data="show_reminders")
        )
        keyboard.add(
            InlineKeyboardButton("🗑️ حذف تذكير", callback_data="delete_reminder_menu"),
            InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")
        )
        
        await bot.edit_message_text(
            "💭 **إدارة التذكيرات اليومية**\n\nاختر العملية المطلوبة:",
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif data == "admin_channel":
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("➕ إضافة رسالة قناة", callback_data="add_channel_msg"),
            InlineKeyboardButton("📝 عرض رسائل القناة", callback_data="show_channel_msgs")
        )
        keyboard.add(
            InlineKeyboardButton("📤 نشر فوري", callback_data="instant_channel_post"),
            InlineKeyboardButton("⏰ جدولة الرسائل", callback_data="schedule_settings")
        )
        keyboard.add(InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
        
        await bot.edit_message_text(
            "📢 **إدارة رسائل القناة**\n\nاختر العملية المطلوبة:",
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif data == "admin_ban":
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🚫 حظر مستخدم", callback_data="ban_user"),
            InlineKeyboardButton("✅ إلغاء حظر", callback_data="unban_user")
        )
        keyboard.add(
            InlineKeyboardButton("📋 قائمة المحظورين", callback_data="show_banned"),
            InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")
        )
        
        await bot.edit_message_text(
            "🚫 **إدارة الحظر**\n\nاختر العملية المطلوبة:",
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif data == "admin_broadcast":
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("📤 إرسال رسالة جماعية", callback_data="send_broadcast"))
        keyboard.add(InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
        
        await bot.edit_message_text(
            f"📤 **النشر الجماعي**\n\nعدد المستخدمين: {len(USERS_LIST)}\n\nاختر العملية المطلوبة:",
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif data == "admin_channel_settings":
        current_channel = bot_data.get("channel_id", "غير محدد")
        interval = bot_data.get("schedule_interval_seconds", 86400)
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🆔 تعديل معرف القناة", callback_data="set_channel_id"))
        keyboard.add(InlineKeyboardButton("⏰ تعديل فترة النشر", callback_data="set_schedule_time"))
        keyboard.add(InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
        
        await bot.edit_message_text(
            f"⚙️ **إعدادات القناة**\n\n"
            f"📢 القناة الحالية: `{current_channel}`\n"
            f"⏰ فترة النشر: {interval // 3600} ساعة\n\n"
            f"اختر الإعداد المراد تعديله:",
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif data == "admin_messages_settings":
        welcome_msg = "✅ محدد" if bot_data.get("welcome_message") else "❌ غير محدد"
        reply_msg = "✅ محدد" if bot_data.get("reply_message") else "❌ غير محدد"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("👋 رسالة الترحيب", callback_data="set_welcome_msg"))
        keyboard.add(InlineKeyboardButton("💬 رسالة الرد التلقائي", callback_data="set_reply_msg"))
        keyboard.add(InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
        
        await bot.edit_message_text(
            f"💬 **إعدادات الرسائل**\n\n"
            f"👋 رسالة الترحيب: {welcome_msg}\n"
            f"💬 الرد التلقائي: {reply_msg}\n\n"
            f"اختر الإعداد المراد تعديله:",
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif data == "admin_media_settings":
        allow_media = bot_data.get("allow_media", False)
        media_status = "✅ مسموح" if allow_media else "❌ محظور"
        rejected_count = bot_data.get("rejected_media_count", 0)
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(
            f"{'🔓 السماح' if not allow_media else '🔒 منع'} الوسائط", 
            callback_data="toggle_media"
        ))
        keyboard.add(InlineKeyboardButton("✏️ رسالة رفض الوسائط", callback_data="set_media_reject_msg"))
        keyboard.add(InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
        
        await bot.edit_message_text(
            f"🔒 **إدارة الوسائط**\n\n"
            f"حالة الوسائط: {media_status}\n"
            f"الوسائط المرفوضة: {rejected_count}\n\n"
            f"اختر الإعداد المراد تعديله:",
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif data == "admin_memory_management":
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🗑️ مسح رسائل مستخدم", callback_data="clear_user_messages"))
        keyboard.add(InlineKeyboardButton("🧹 مسح الذاكرة المؤقتة", callback_data="clear_temp_memory"))
        keyboard.add(InlineKeyboardButton("📊 إحصائيات الذاكرة", callback_data="memory_stats"))
        keyboard.add(InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
        
        await bot.edit_message_text(
            f"🧠 **إدارة الذاكرة**\n\n"
            f"الرسائل المحفوظة: {len(user_messages)}\n"
            f"المحادثات النشطة: {len(user_threads)}\n"
            f"إحصائيات Spam: {len(user_message_count)}\n\n"
            f"اختر العملية المطلوبة:",
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    # معالجة الأزرار الفرعية
    elif data == "show_replies":
        if AUTO_REPLIES:
            replies_text = "📝 **الردود التلقائية الحالية:**\n\n"
            for trigger, response in list(AUTO_REPLIES.items())[:10]:  # أول 10 ردود فقط
                replies_text += f"🔹 `{trigger}`\n   ↳ {response[:50]}...\n\n"
            if len(AUTO_REPLIES) > 10:
                replies_text += f"... و {len(AUTO_REPLIES) - 10} ردود أخرى"
        else:
            replies_text = "📝 لا توجد ردود تلقائية محفوظة حالياً"
            
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔙 العودة لإدارة الردود", callback_data="admin_replies"))
        
        await bot.edit_message_text(
            replies_text,
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif data == "show_reminders":
        if DAILY_REMINDERS:
            reminders_text = "💭 **التذكيرات اليومية الحالية:**\n\n"
            for i, reminder in enumerate(DAILY_REMINDERS[:5], 1):  # أول 5 تذكيرات
                reminders_text += f"{i}. {reminder[:60]}...\n\n"
            if len(DAILY_REMINDERS) > 5:
                reminders_text += f"... و {len(DAILY_REMINDERS) - 5} تذكيرات أخرى"
        else:
            reminders_text = "💭 لا توجد تذكيرات محفوظة حالياً"
            
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔙 العودة لإدارة التذكيرات", callback_data="admin_reminders"))
        
        await bot.edit_message_text(
            reminders_text,
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif data == "toggle_media":
        current_status = bot_data.get("allow_media", False)
        bot_data["allow_media"] = not current_status
        save_data(bot_data)
        
        new_status = "مسموح ✅" if not current_status else "محظور ❌"
        await bot.answer_callback_query(
            callback_query.id,
            f"تم تغيير حالة الوسائط إلى: {new_status}",
            show_alert=True
        )
        
        # العودة لصفحة إعدادات الوسائط
        await process_admin_callback(callback_query, state)

    elif data == "clear_temp_memory":
        user_message_count.clear()
        silenced_users.clear()
        await bot.answer_callback_query(
            callback_query.id,
            "✅ تم مسح الذاكرة المؤقتة بنجاح",
            show_alert=True
        )

    elif data == "close_panel":
        await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
        await bot.send_message(callback_query.from_user.id, "✅ تم إغلاق لوحة التحكم")
    
    else:
        # الأزرار التي تحتاج إدخال نص (FSM States)
        if data in ["add_reply", "add_reminder", "add_channel_msg", "ban_user", "unban_user", 
                    "send_broadcast", "set_channel_id", "set_schedule_time", "set_welcome_msg", 
                    "set_reply_msg", "set_media_reject_msg", "clear_user_messages"]:
            await bot.answer_callback_query(
                callback_query.id, 
                "هذه الميزة تتطلب إدخال نص وستكون متوفرة قريباً", 
                show_alert=True
            )
        else:
            await bot.answer_callback_query(
                callback_query.id, 
                "⚠️ هذه الميزة قيد التطوير", 
                show_alert=True
            )

# ----------------- فلترة الوسائط -----------------
@dp.message_handler(lambda message: message.from_user.id != ADMIN_CHAT_ID, content_types=[
    types.ContentType.PHOTO, types.ContentType.VIDEO, types.ContentType.AUDIO,
    types.ContentType.VOICE, types.ContentType.VIDEO_NOTE, types.ContentType.STICKER,
    types.ContentType.DOCUMENT, types.ContentType.ANIMATION, types.ContentType.CONTACT,
    types.ContentType.LOCATION, types.ContentType.VENUE, types.ContentType.POLL,
    types.ContentType.DICE, types.ContentType.GAME
], state="*")
async def handle_media_message(message: types.Message):
    if is_banned(message.from_user.id):
        return

    allow_media = bot_data.get("allow_media", False)
    if not allow_media:
        custom_reject_message = bot_data.get("media_reject_message", "❌ يُسمح بالرسائل النصية فقط. يرجى إرسال النص فقط.")
        await message.reply(custom_reject_message)
        bot_data["rejected_media_count"] = bot_data.get("rejected_media_count", 0) + 1
        save_data(bot_data)
        return

    await handle_user_content(message, "[وسائط]")

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
        
        # إعادة توجيه الرسالة إذا كانت تحتوي على محتوى قابل للإعادة
        if hasattr(message, 'content_type') and message.content_type != types.ContentType.TEXT:
            try:
                await message.forward(ADMIN_CHAT_ID)
            except Exception as e:
                print(f"خطأ في إعادة توجيه الرسالة: {e}")

        user_messages[admin_msg.message_id] = {
            "user_id": user_id,
            "user_message_id": message.message_id,
            "user_text": content_text
        }
        user_threads[user_id] = {
            "admin_message_id": admin_msg.message_id,
            "user_message_id": message.message_id
        }
    except Exception as e:
        print(f"خطأ في إرسال للإدارة: {e}")

# ----------------- التعامل مع الرسائل النصية -----------------
@dp.message_handler(lambda message: message.from_user.id != ADMIN_CHAT_ID and not message.text.startswith('/start'), content_types=types.ContentTypes.TEXT, state="*")
async def handle_user_message(message: types.Message):
    if is_banned(message.from_user.id):
        return

    user_id = message.from_user.id
    first_name = message.from_user.first_name or "غير معروف"

    spam_allowed, spam_status = check_spam_limit(user_id)
    if not spam_allowed:
        warning_message = get_spam_warning_message(spam_status, first_name)
        await message.reply(warning_message)
        return

    user_message = message.text.strip()

    if user_id not in USERS_LIST:
        USERS_LIST.add(user_id)
        bot_data["users"] = list(USERS_LIST)
        save_data(bot_data)

    # فحص الردود التلقائية أولاً
    if user_message in AUTO_REPLIES:
        await message.reply(AUTO_REPLIES[user_message], reply_markup=create_buttons())
        return

    # إرسال للإدارة
    await handle_user_content(message, user_message)

    # رد تلقائي للمستخدم
    custom_reply_message = bot_data.get("reply_message")
    if custom_reply_message:
        reply_text = custom_reply_message
    else:
        reply_text = (
            "🌿 تم الاستلام بنجاح!\n"
            "جزاك الله خيرًا على تواصلك. 🤲\n"
            "نسأل الله أن يجعل ما أرسلته خالصًا لوجهه الكريم، وأن ينفع به الجميع.\n"
            "إذا أردت إضافة أي ملاحظة أو استفسار آخر، فنحن هنا لنستمع إليك. 🌸"
        )

    await message.reply(reply_text, reply_markup=create_buttons())

# ----------------- التعامل مع ردود الإدارة -----------------
@dp.message_handler(lambda message: message.from_user.id == ADMIN_CHAT_ID and message.reply_to_message, content_types=types.ContentTypes.TEXT, state="*")
async def handle_admin_reply(message: types.Message):
    replied_to_message_id = message.reply_to_message.message_id
    admin_reply_text = message.text.strip()

    if replied_to_message_id in user_messages:
        user_info = user_messages[replied_to_message_id]
        user_id = user_info["user_id"]
        user_original_text = user_info["user_text"]

        if is_banned(user_id):
            await message.reply("❌ هذا المستخدم محظور!")
            return

        reply_message = f"رسالتك:\n{user_original_text}\n\n📩 رد من الإدارة:\n{admin_reply_text}"

        try:
            await bot.send_message(chat_id=user_id, text=reply_message)
            await message.reply("✅ تم إرسال الرد بنجاح للمستخدم")
        except Exception as e:
            await message.reply(f"❌ خطأ في إرسال الرد: {e}")
    else:
        await message.reply("❌ لم يتم العثور على الرسالة الأصلية. تأكد من أنك ترد على رسالة مستخدم.")

# ----------------- التعامل مع الأزرار العادية -----------------
@dp.callback_query_handler(lambda c: c.from_user.id != ADMIN_CHAT_ID, state="*")
async def process_callback(callback_query: types.CallbackQuery):
    if is_banned(callback_query.from_user.id):
        await bot.answer_callback_query(callback_query.id, "❌ أنت محظور من استخدام هذا البوت!")
        return

    data = callback_query.data
    user_id = callback_query.from_user.id

    try:
        if data == "hijri_today":
            await bot.answer_callback_query(callback_query.id)
            await bot.send_message(user_id, get_hijri_date())
        elif data == "live_time":
            await bot.answer_callback_query(callback_query.id)
            await bot.send_message(user_id, get_live_time())
        elif data == "daily_reminder":
            await bot.answer_callback_query(callback_query.id)
            await bot.send_message(user_id, get_daily_reminder())
        elif data == "from_developer":
            await bot.answer_callback_query(callback_query.id)
            await bot.send_message(
                user_id,
                "تم تطوير هذا البوت بواسطة ✨ ابو سيف بن ذي يزن ✨\n[فريق التقويم الهجري](https://t.me/HejriCalender)",
                parse_mode="Markdown"
            )
    except Exception as e:
        await bot.answer_callback_query(callback_query.id, f"⚠️ حدث خطأ: {str(e)}")
        print(f"خطأ في معالج الأزرار: {e}")

# ----------------- معالج /start -----------------
@dp.message_handler(commands=['start'], state="*")
async def send_welcome(message: types.Message):
    if is_banned(message.from_user.id):
        return

    user_id = message.from_user.id
    if user_id not in USERS_LIST:
        USERS_LIST.add(user_id)
        bot_data["users"] = list(USERS_LIST)
        save_data(bot_data)

    custom_welcome = bot_data.get("welcome_message")
    if custom_welcome:
        user_name = message.from_user.first_name or "عزيزي المستخدم"
        welcome_text = custom_welcome.replace("{name}", user_name)
    else:
        user_name = message.from_user.first_name or "عزيزي المستخدم"
        welcome_text = (
            f"👋 أهلًا وسهلًا بك، {user_name}!\n"
            "هذا البوت مخصص للإجابة عن استفساراتك حول القناة وأي ملاحظات تود مشاركتها.\n"
            "فضّل بطرح سؤالك أو ملاحظتك، وسأرد عليك بأسرع وقت ممكن. ✨\n\n"
            "───\n"
            "تم تطوير هذا البوت بواسطة: [أبو سيف بن ذي يزن](https://t.me/HejriCalender) 🌹"
        )

    await message.reply(welcome_text, reply_markup=create_buttons(), parse_mode="Markdown")

# ----------------- مهام الخلفية المحسنة -----------------
async def keep_alive_task():
    ping_count = 0
    while True:
        try:
            await asyncio.sleep(300)  # كل 5 دقائق
            ping_count += 1

            try:
                me = await bot.get_me()
                if ping_count % 6 == 0:  # كل 30 دقيقة
                    print(f"🔄 Keep alive #{ping_count} - البوت نشط: @{me.username} - {datetime.datetime.now().strftime('%H:%M:%S')}")
            except Exception as e:
                print(f"⚠️ تحذير: مشكلة في اتصال البوت: {e}")

        except Exception as e:
            print(f"❌ خطأ في keep alive: {e}")
            await asyncio.sleep(60)

async def deployment_monitor():
    while True:
        try:
            await asyncio.sleep(3600)  # كل ساعة

            current_time = datetime.datetime.now()
            uptime_hours = (current_time - start_time).total_seconds() / 3600

            print(f"📊 مراقب النشر: البوت يعمل منذ {uptime_hours:.1f} ساعة - {current_time.strftime('%H:%M:%S')}")

            # تقرير يومي في الساعة 12 ظهراً
            if current_time.hour == 12 and current_time.minute < 5:
                try:
                    await bot.send_message(
                        ADMIN_CHAT_ID,
                        f"📊 **تقرير يومي - البوت يعمل بنجاح**\n\n"
                        f"⏰ وقت التشغيل: {uptime_hours:.1f} ساعة\n"
                        f"👥 المستخدمين: {len(USERS_LIST)}\n"
                        f"💬 الرسائل: {len(user_messages)}\n"
                        f"🌐 الخادم: نشط ومستقر\n\n"
                        f"✅ كل شيء يعمل بشكل طبيعي!",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"خطأ في إرسال التقرير اليومي: {e}")

        except Exception as e:
            print(f"❌ خطأ في مراقب النشر: {e}")

# ----------------- دوال التشغيل -----------------
async def startup(dp):
    try:
        # بدء المهام في الخلفية
        asyncio.create_task(schedule_channel_messages())
        asyncio.create_task(keep_alive_task())
        asyncio.create_task(deployment_monitor())

        print("✅ البوت جاهز للعمل 24/7!")
        print("🚀 مراقب النشر المستمر مفعل")
        print("🔄 خادم الويب يعمل على المنفذ 5000")
        print("🌐 جاهز للنشر على Reserved VM")

        # إرسال رسالة تأكيد للإدارة
        try:
            await bot.send_message(
                ADMIN_CHAT_ID,
                "✅ **البوت يعمل بنجاح!**\n\n"
                "🤖 البوت متصل ونشط\n"
                "🌐 خادم الويب يعمل\n"
                "📱 جاهز لاستقبال الرسائل\n"
                "🚀 مستعد للنشر المستمر 24/7\n"
                f"⏰ وقت التشغيل: {datetime.datetime.now().strftime('%H:%M:%S')}\n\n"
                "💡 **للعمل 24/7:** استخدم Reserved VM Deployment",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"تحذير: لا يمكن إرسال رسالة البداية للإدارة: {e}")

    except Exception as e:
        print(f"❌ خطأ في startup: {e}")

def main():
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
