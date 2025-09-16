import os
import datetime
import json
import asyncio
import random
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("🔍 فحص متغيرات البيئة...")

API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    logging.critical("❌ خطأ: متغير البيئة BOT_TOKEN غير موجود!")
    exit(1)

ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
if not ADMIN_CHAT_ID:
    logging.critical("❌ خطأ: متغير البيئة ADMIN_CHAT_ID غير موجود!")
    exit(1)

try:
    ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)
    logging.info(f"✅ تم تعيين المشرف: {ADMIN_CHAT_ID}")
except ValueError:
    logging.critical("❌ خطأ: ADMIN_CHAT_ID يجب أن يكون رقماً صحيحاً")
    exit(1)

logging.info("✅ جميع متغيرات البيئة صحيحة")

CHANNEL_ID = os.getenv("CHANNEL_ID")

storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

start_time = datetime.datetime.now()

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

DATABASE_FILE = "bot_data.json"

def load_data():
    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "auto_replies": {}, "daily_reminders": [], "channel_messages": [],
            "banned_users": [], "users": [], "channel_id": "", "allow_media": False,
            "media_reject_message": "❌ يُسمح بالرسائل النصية فقط.",
            "rejected_media_count": 0, "welcome_message": "", "reply_message": "",
            "schedule_interval_seconds": 86400
        }
    except json.JSONDecodeError:
        logging.error(f"خطأ في قراءة ملف {DATABASE_FILE}. سيتم استخدام البيانات الافتراضية.")
        return {}

def save_data(data):
    try:
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"خطأ في حفظ البيانات: {e}")

bot_data = load_data()

USERS_LIST = set(bot_data.get("users", []))
BANNED_USERS = set(bot_data.get("banned_users", []))

AUTO_REPLIES = {
    "السلام عليكم": "وعليكم السلام ورحمة الله وبركاته 🌹",
    "مرحبا": "مرحباً بك 🌙",
    "كيف حالك": "الحمد لله بخير 🤲",
    "شكرا": "العفو 🌹",
    "جزاك الله خير": "وإياك أجمعين يا رب 🤲",
}
AUTO_REPLIES.update(bot_data.get("auto_replies", {}))

DAILY_REMINDERS = [
    "🌅 سبحان الله وبحمده، سبحان الله العظيم.",
    "🤲 اللهم أعني على ذكرك وشكرك وحسن عبادتك.",
    "💎 لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير.",
]
DAILY_REMINDERS.extend(bot_data.get("daily_reminders", []))

CHANNEL_MESSAGES = [
    "🌙 بسم الله نبدأ يوماً جديداً\n\n💎 قال تعالى: {وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا}",
    "🌟 تذكير إيماني\n\n📖 قال رسول الله ﷺ: (إن الله جميل يحب الجمال)",
]
CHANNEL_MESSAGES.extend(bot_data.get("channel_messages", []))

user_messages = {}
user_threads = {}
user_message_count = {}
silenced_users = {}

def is_banned(user_id):
    return user_id in BANNED_USERS

def check_spam_limit(user_id):
    current_time = datetime.datetime.now()
    if user_id in silenced_users:
        if (current_time - silenced_users[user_id]).total_seconds() < 30:
            return False, "silenced"
        else:
            del silenced_users[user_id]
    
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
        return f"⚠️ عذراً {user_name}، لقد تجاوزت حد الرسائل. تم إيقافك مؤقتاً لمدة 30 ثانية."
    elif status == "silenced":
        return "🔇 أنت موقوف مؤقتاً. يرجى الانتظار."
    return ""

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

def get_hijri_date():
    try:
        from hijri_converter import convert
        today = datetime.date.today()
        hijri_date = convert.Gregorian(today.year, today.month, today.day).to_hijri()
        hijri_months = {
            1: "محرم", 2: "صفر", 3: "ربيع الأول", 4: "ربيع الآخر", 5: "جمادى الأولى", 
            6: "جمادى الآخرة", 7: "رجب", 8: "شعبان", 9: "رمضان", 10: "شوال", 
            11: "ذو القعدة", 12: "ذو الحجة"
        }
        weekdays = {0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"}
        return (f"🌙 التاريخ الهجري اليوم:\n"
                f"📅 {hijri_date.day} {hijri_months[hijri_date.month]} {hijri_date.year} هـ\n"
                f"📆 {weekdays[today.weekday()]}\n\n"
                f"📅 التاريخ الميلادي:\n"
                f"🗓️ {today.strftime('%d/%m/%Y')} م")
    except ImportError:
        logging.warning("مكتبة hijri-converter غير مثبتة.")
        return "🌙 لعرض التاريخ الهجري، يجب تثبيت مكتبة `hijri-converter`."
    except Exception as e:
        logging.error(f"خطأ في جلب التاريخ الهجري: {e}")
        return "🌙 عذراً، حدث خطأ في جلب التاريخ."

def get_daily_reminder():
    return random.choice(DAILY_REMINDERS)

def get_live_time():
    try:
        import pytz
        riyadh_tz = pytz.timezone('Asia/Riyadh')
        now = datetime.datetime.now(riyadh_tz)
    except ImportError:
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
    
    weekdays = {0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"}
    months = {
        1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو", 
        7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
    }
    return (f"🕐 الساعة الآن: {now.strftime('%H:%M:%S')}\n"
            f"📅 التاريخ: {weekdays[now.weekday()]} - {now.day} {months[now.month]} {now.year}\n"
            f"🕌 بتوقيت مدينة الرياض")

async def send_channel_message(custom_message=None, channel_id_override=None):
    channel_id = channel_id_override or bot_data.get("channel_id") or CHANNEL_ID
    if not channel_id or not CHANNEL_MESSAGES:
        logging.warning("النشر التلقائي متوقف: معرف القناة أو الرسائل غير متوفرة.")
        return False
    try:
        message = custom_message or random.choice(CHANNEL_MESSAGES)
        if not channel_id.startswith('@') and not channel_id.startswith('-'):
            channel_id = '@' + channel_id
        await bot.send_message(chat_id=channel_id, text=message)
        logging.info(f"✅ تم إرسال رسالة للقناة: {channel_id}")
        return True
    except Exception as e:
        logging.error(f"❌ خطأ في إرسال الرسالة للقناة {channel_id}: {e}")
        return False

async def schedule_channel_messages():
    logging.info("🕐 بدء جدولة الرسائل التلقائية للقناة...")
    while True:
        try:
            interval_seconds = bot_data.get("schedule_interval_seconds", 86400)
            await asyncio.sleep(interval_seconds)
            await send_channel_message()
        except Exception as e:
            logging.error(f"❌ خطأ في جدولة الرسائل: {e}")
            await asyncio.sleep(60)

@dp.message_handler(lambda message: message.from_user.id == ADMIN_CHAT_ID and message.text == "/admin", state="*")
async def admin_panel(message: types.Message):
    await message.reply("🔧 **لوحة التحكم الإدارية**", reply_markup=create_admin_panel(), parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.from_user.id == ADMIN_CHAT_ID, state="*")
async def process_admin_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id

    actions = {
        "admin_replies": "📝 **إدارة الردود التلقائية**",
        "admin_reminders": "💭 **إدارة التذكيرات اليومية**",
        "admin_channel": "📢 **إدارة رسائل القناة**",
        "admin_ban": "🚫 **إدارة الحظر**",
    }
    keyboards = {
        "admin_replies": InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton("➕ إضافة", callback_data="add_reply"), InlineKeyboardButton("📝 عرض", callback_data="show_replies"), InlineKeyboardButton("🗑️ حذف", callback_data="delete_reply_menu"), InlineKeyboardButton("🔙 عودة", callback_data="back_to_main")),
        "admin_reminders": InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton("➕ إضافة", callback_data="add_reminder"), InlineKeyboardButton("📝 عرض", callback_data="show_reminders"), InlineKeyboardButton("🗑️ حذف", callback_data="delete_reminder_menu"), InlineKeyboardButton("🔙 عودة", callback_data="back_to_main")),
        "admin_channel": InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton("➕ إضافة", callback_data="add_channel_msg"), InlineKeyboardButton("📝 عرض", callback_data="show_channel_msgs"), InlineKeyboardButton("📤 نشر فوري", callback_data="instant_channel_post"), InlineKeyboardButton("🔙 عودة", callback_data="back_to_main")),
        "admin_ban": InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton("🚫 حظر", callback_data="ban_user"), InlineKeyboardButton("✅ إلغاء", callback_data="unban_user"), InlineKeyboardButton("📋 عرض", callback_data="show_banned"), InlineKeyboardButton("🔙 عودة", callback_data="back_to_main")),
    }

    if data in actions:
        await bot.edit_message_text(actions[data], chat_id=user_id, message_id=message_id, reply_markup=keyboards[data])
    elif data == "admin_stats":
        stats_text = (f"📊 **إحصائيات البوت**\n\n"
                      f"الردود: {len(AUTO_REPLIES)} | التذكيرات: {len(DAILY_REMINDERS)}\n"
                      f"رسائل القناة: {len(CHANNEL_MESSAGES)} | المحظورين: {len(BANNED_USERS)}\n"
                      f"إجمالي المستخدمين: {len(USERS_LIST)}")
        await bot.edit_message_text(stats_text, chat_id=user_id, message_id=message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 عودة", callback_data="back_to_main")), parse_mode="Markdown")
    elif data == "back_to_main":
        await bot.edit_message_text("🔧 **لوحة التحكم الإدارية**", chat_id=user_id, message_id=message_id, reply_markup=create_admin_panel(), parse_mode="Markdown")
    elif data == "close_panel":
        await bot.delete_message(user_id, message_id)
    else:
        await bot.answer_callback_query(callback_query.id, "⚠️ هذه الميزة قيد التطوير", show_alert=True)


@dp.message_handler(lambda message: message.from_user.id != ADMIN_CHAT_ID, content_types=types.ContentTypes.ANY, state="*")
async def handle_any_message(message: types.Message):
    user_id = message.from_user.id
    if is_banned(user_id): return

    first_name = message.from_user.first_name or ""
    spam_allowed, spam_status = check_spam_limit(user_id)
    if not spam_allowed:
        await message.reply(get_spam_warning_message(spam_status, first_name))
        return

    if user_id not in USERS_LIST:
        USERS_LIST.add(user_id)
        bot_data["users"] = list(USERS_LIST)
        save_data(bot_data)
        logging.info(f"مستخدم جديد: {first_name} ({user_id}). الإجمالي: {len(USERS_LIST)}")

    content_text = ""
    if message.content_type == types.ContentType.TEXT:
        if message.text.strip() == '/start': return
        if message.text in AUTO_REPLIES:
            await message.reply(AUTO_REPLIES[message.text], reply_markup=create_buttons())
            return
        content_text = message.text
        reply_text = bot_data.get("reply_message") or "🌿 تم استلام رسالتك بنجاح، شكراً لتواصلك."
        await message.reply(reply_text, reply_markup=create_buttons())
    else:
        if not bot_data.get("allow_media", False):
            await message.reply(bot_data.get("media_reject_message", "❌ الوسائط غير مسموحة."))
            bot_data["rejected_media_count"] = bot_data.get("rejected_media_count", 0) + 1
            save_data(bot_data)
            return
        content_text = f"[{message.content_type.upper()}]"
    
    await handle_user_content(message, content_text)

async def handle_user_content(message, content_text=""):
    try:
        fwd_msg = await message.forward(ADMIN_CHAT_ID)
        admin_text = f"📩 من: {message.from_user.full_name} (`{message.from_user.id}`)"
        info_msg = await bot.send_message(ADMIN_CHAT_ID, admin_text, reply_to_message_id=fwd_msg.message_id, parse_mode="Markdown")
        user_messages[info_msg.message_id] = {"user_id": message.from_user.id}
    except Exception as e:
        logging.error(f"خطأ في توجيه الرسالة للمشرف: {e}")

@dp.message_handler(lambda message: message.from_user.id == ADMIN_CHAT_ID and message.reply_to_message, content_types=types.ContentTypes.ANY, state="*")
async def handle_admin_reply(message: types.Message):
    replied_msg = message.reply_to_message
    target_info = user_messages.get(replied_msg.message_id)

    if not target_info and replied_msg.forward_from:
        user_id_from_fwd = replied_msg.forward_from.id
        # Fallback to find user by forwarded message
        for info in user_messages.values():
            if info.get('user_id') == user_id_from_fwd:
                target_info = info
                break
    
    if target_info:
        user_id = target_info["user_id"]
        if is_banned(user_id):
            await message.reply("❌ المستخدم محظور.")
            return
        try:
            await message.copy_to(chat_id=user_id)
            await message.reply("✅ تم إرسال الرد.")
        except Exception as e:
            await message.reply(f"❌ خطأ في إرسال الرد: {e}")
    else:
        await message.reply("⚠️ لم يتم العثور على المستخدم المرتبط بهذه الرسالة.")

@dp.callback_query_handler(lambda c: c.from_user.id != ADMIN_CHAT_ID, state="*")
async def process_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if is_banned(user_id):
        await bot.answer_callback_query(callback_query.id, "❌ أنت محظور!")
        return
    
    actions = {
        "hijri_today": get_hijri_date,
        "live_time": get_live_time,
        "daily_reminder": get_daily_reminder,
    }
    
    try:
        if callback_query.data in actions:
            await bot.send_message(user_id, actions[callback_query.data]())
        elif callback_query.data == "from_developer":
            await bot.send_message(user_id, "تم تطوير هذا البوت بواسطة ✨ ابو سيف بن ذي يزن ✨\n[فريق التقويم الهجري](https://t.me/HejriCalender)", parse_mode="Markdown")
        await bot.answer_callback_query(callback_query.id)
    except Exception as e:
        logging.error(f"خطأ في معالج الأزرار: {e}")
        await bot.answer_callback_query(callback_query.id, "⚠️ حدث خطأ.")

@dp.message_handler(commands=['start'], state="*")
async def send_welcome(message: types.Message):
    if is_banned(message.from_user.id): return

    user_id = message.from_user.id
    user_name = message.from_user.first_name or "المستخدم"
    
    custom_welcome = bot_data.get("welcome_message")
    if custom_welcome:
        welcome_text = custom_welcome.replace("{name}", user_name)
    else:
        welcome_text = (f"👋 أهلًا بك، {user_name}!\n"
                        "هذا البوت مخصص للتواصل مع إدارة القناة.\n"
                        "تفضل بطرح سؤالك أو ملاحظتك. ✨")
    
    await message.reply(welcome_text, reply_markup=create_buttons(), parse_mode="Markdown")

async def on_startup(dp):
    asyncio.create_task(schedule_channel_messages())
    logging.info("✅ البوت جاهز للعمل!")
    await bot.send_message(ADMIN_CHAT_ID, "✅ **البوت يعمل الآن!**", parse_mode="Markdown")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)


