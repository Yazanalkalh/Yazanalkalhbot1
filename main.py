# -*- coding: utf-8 -*-
import os
import datetime
import json
import asyncio
import random
from threading import Thread

# ----------------- فحص وتشغيل خادم الويب (مهم جداً لـ Render) -----------------
# هذا الخادم ضروري لإبقاء البوت نشطاً على منصات الاستضافة مثل Render
try:
    from webserver import start_webserver
    print("🌐 attempting to start Flask web server...")
    if start_webserver():
        print("✅ Flask web server is running in the background.")
    else:
        print("⚠️ Failed to start Flask web server.")
except ImportError:
    print("⚠️ 'webserver.py' not found. The bot might not stay awake on Render.")
except Exception as e:
    print(f"⚠️ An error occurred with the web server: {e}")

# ----------------- استيراد مكتبات aiogram -----------------
try:
    from aiogram import Bot, Dispatcher, types, executor
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.dispatcher import FSMContext
    from aiogram.dispatcher.filters.state import State, StatesGroup
    from aiogram.contrib.fsm_storage.memory import MemoryStorage
    print("✅ aiogram libraries imported successfully.")
except ImportError:
    print("❌ Critical Error: 'aiogram' is not installed. Please run 'pip install aiogram'.")
    exit(1)


# ----------------- إعداد متغيرات البيئة -----------------
print("🔍 Checking environment variables...")

API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    print("❌ ERROR: BOT_TOKEN environment variable not found!")
    print("📝 Please add BOT_TOKEN in the Secrets (Environment) tab.")
    exit(1)

ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
if not ADMIN_CHAT_ID:
    print("❌ ERROR: ADMIN_CHAT_ID environment variable not found!")
    print("📝 Please add ADMIN_CHAT_ID in the Secrets (Environment) tab.")
    exit(1)

try:
    ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)
    print(f"✅ Admin ID set to: {ADMIN_CHAT_ID}")
except ValueError:
    print("❌ ERROR: ADMIN_CHAT_ID must be a valid integer.")
    exit(1)

# معرف القناة (اختياري)
CHANNEL_ID = os.getenv("CHANNEL_ID", "") # Provide a default empty value
print("✅ Environment variables loaded.")

# ----------------- إعداد البوت و FSM -----------------
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
    # ... add other states as needed

# ----------------- إدارة قاعدة البيانات (JSON) -----------------
# For Render's persistent storage (Disks), we must use a fixed path.
# تأكد من إنشاء قرص (Disk) في Render وتعيين مسار التحميل (Mount Path) إلى /var/data
RENDER_DISK_PATH = "/var/data"
DATABASE_FILE = os.path.join(RENDER_DISK_PATH, "bot_data.json")

def load_data():
    # Ensure the directory for the database exists
    if not os.path.exists(RENDER_DISK_PATH):
        # If not on Render, this directory might not exist. Create it or use local dir.
        if "RENDER" in os.environ:
             print(f"Error: Disk mount path {RENDER_DISK_PATH} not found!")
             # In a real Render environment, this path should exist.
             # For robustness, we can try to create it, though it may fail.
             try:
                 os.makedirs(RENDER_DISK_PATH, exist_ok=True)
             except OSError as e:
                 print(f"Could not create directory {RENDER_DISK_PATH}: {e}")
                 # Fallback to local directory if on Render but disk is not attached
                 global DATABASE_FILE
                 DATABASE_FILE = "bot_data.json"
                 print("Warning: Falling back to local storage. Data will NOT be persistent on Render restarts.")
        else:
             # Not on Render, use local directory for testing.
             DATABASE_FILE = "bot_data.json"


    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            print(f"✅ Loading data from {DATABASE_FILE}")
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Data file not found at {DATABASE_FILE}. Creating a new one.")
        return {
            "auto_replies": {}, "daily_reminders": [], "channel_messages": [],
            "banned_users": [], "users": [], "channel_id": CHANNEL_ID,
            "allow_media": False, "media_reject_message": "❌ يُسمح بالرسائل النصية فقط.",
            "rejected_media_count": 0, "welcome_message": "", "reply_message": "",
            "schedule_interval_seconds": 86400
        }
    except json.JSONDecodeError:
        print(f"❌ Error decoding JSON from {DATABASE_FILE}. Starting with a fresh database.")
        return {} # Return empty dict to be populated by .get() defaults

def save_data(data):
    try:
        # Create a temporary file and write to it, then rename. This is safer.
        temp_file = DATABASE_FILE + ".tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.replace(temp_file, DATABASE_FILE)
        # print(f"💾 Data saved successfully to {DATABASE_FILE}") # Can be too noisy
    except Exception as e:
        print(f"❌ CRITICAL ERROR saving data: {e}")

bot_data = load_data()

# ----------------- تحميل الإعدادات من قاعدة البيانات -----------------
USERS_LIST = set(bot_data.get("users", []))
BANNED_USERS = set(bot_data.get("banned_users", []))
AUTO_REPLIES = bot_data.get("auto_replies", {})
DAILY_REMINDERS = bot_data.get("daily_reminders", [])
CHANNEL_MESSAGES = bot_data.get("channel_messages", [])

# إضافة الردود والتذكيرات الافتراضية إذا كانت القائمة فارغة
if not AUTO_REPLIES:
    AUTO_REPLIES.update({
        "السلام عليكم": "وعليكم السلام ورحمة الله وبركاته 🌹",
        "مرحبا": "مرحباً بك 🌙",
        "شكرا": "العفو 🌹",
    })
if not DAILY_REMINDERS:
    DAILY_REMINDERS.extend([
        "🌅 سبحان الله وبحمده، سبحان الله العظيم 🌙",
        "🤲 اللهم أعني على ذكرك وشكرك وحسن عبادتك ✨",
    ])
if not CHANNEL_MESSAGES:
    CHANNEL_MESSAGES.extend([
        "🌙 بسم الله نبدأ يوماً جديداً. اللهم اجعل هذا اليوم خيراً وبركة علينا جميعاً.",
        "🌟 تذكير إيماني: قال رسول الله ﷺ: (إن الله جميل يحب الجمال).",
    ])


# ----------------- نظام منع السبام (Anti-Spam) -----------------
user_message_timestamps = {}
SPAM_LIMIT = 5  # messages
SPAM_TIMEFRAME = 10  # seconds

def is_spam(user_id):
    current_time = datetime.datetime.now().timestamp()
    if user_id not in user_message_timestamps:
        user_message_timestamps[user_id] = []

    # إزالة الطوابع الزمنية القديمة
    user_message_timestamps[user_id] = [t for t in user_message_timestamps[user_id] if current_time - t < SPAM_TIMEFRAME]

    # إضافة الطابع الزمني الحالي
    user_message_timestamps[user_id].append(current_time)

    # التحقق من تجاوز الحد
    if len(user_message_timestamps[user_id]) > SPAM_LIMIT:
        return True
    return False

# ----------------- دوال مساعدة -----------------
def is_banned(user_id):
    return user_id in BANNED_USERS

# ... (بقية الدوال مثل get_hijri_date, get_daily_reminder, create_buttons, etc.)
# لا حاجة لتغييرها، الكود الأصلي هنا جيد
def get_hijri_date():
    try:
        from hijri_converter import convert
        today = datetime.date.today()
        gregorian_date = convert.Gregorian(today.year, today.month, today.day)
        hijri_date = gregorian_date.to_hijri()
        return f"🌙 التاريخ الهجري: {hijri_date.day_name()}، {hijri_date.day} {hijri_date.month_name()} {hijri_date.year} هـ"
    except ImportError:
        return "💡 مكتبة التاريخ الهجري غير مثبتة. لعرض التاريخ، يرجى تثبيت `hijri-converter`."
    except Exception as e:
        return f"⚠️ حدث خطأ في جلب التاريخ الهجري: {e}"

def get_live_time():
    now = datetime.datetime.now()
    return f"🕐 الساعة الآن: {now.strftime('%H:%M:%S')}\n📅 التاريخ: {now.strftime('%Y-%m-%d')}"

def get_daily_reminder():
    return random.choice(DAILY_REMINDERS) if DAILY_REMINDERS else "لا توجد تذكيرات متاحة."

def create_buttons():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📅 اليوم هجري", callback_data="hijri_today"),
        InlineKeyboardButton("🕐 الساعة", callback_data="live_time")
    )
    keyboard.add(InlineKeyboardButton("💡 تذكير يومي", callback_data="daily_reminder"))
    keyboard.add(InlineKeyboardButton("👨‍💻 عن المطور", callback_data="from_developer"))
    return keyboard

def create_admin_panel():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
        InlineKeyboardButton("📤 نشر للجميع", callback_data="admin_broadcast")
    )
    keyboard.add(
        InlineKeyboardButton("🚫 إدارة الحظر", callback_data="admin_ban"),
        InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_settings")
    )
    keyboard.add(InlineKeyboardButton("❌ إغلاق", callback_data="close_panel"))
    return keyboard

# ----------------- معالجات الرسائل والأوامر -----------------

@dp.message_handler(commands=['start'], state="*")
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    if is_banned(user_id):
        return

    if user_id not in USERS_LIST:
        USERS_LIST.add(user_id)
        bot_data["users"] = list(USERS_LIST)
        save_data(bot_data)
        await bot.send_message(ADMIN_CHAT_ID, f"🎉 مستخدم جديد انضم!\nالاسم: {message.from_user.full_name}\nالمعرف: @{message.from_user.username}\nID: `{user_id}`", parse_mode="Markdown")

    user_name = message.from_user.first_name
    welcome_text = bot_data.get("welcome_message", f"👋 أهلًا وسهلًا بك، {user_name}!\nأنا هنا لمساعدتك. تفضل بإرسال رسالتك.").replace("{name}", user_name)
    await message.reply(welcome_text, reply_markup=create_buttons(), parse_mode="Markdown")

@dp.message_handler(lambda message: message.from_user.id == ADMIN_CHAT_ID and message.text == "/admin", state="*")
async def admin_panel_command(message: types.Message):
    await message.reply("🔧 **لوحة تحكم المدير**", reply_markup=create_admin_panel(), parse_mode="Markdown")

# معالج الرد من المدير
@dp.message_handler(lambda message: message.from_user.id == ADMIN_CHAT_ID and message.reply_to_message, content_types=types.ContentTypes.ANY, state="*")
async def handle_admin_reply(message: types.Message):
    original_message_text = message.reply_to_message.text or message.reply_to_message.caption
    if not original_message_text or "ID: `" not in original_message_text:
        await message.reply("⚠️ لا يمكن العثور على ID المستخدم في الرسالة الأصلية. يرجى الرد على رسالة من البوت.")
        return

    try:
        user_id_str = original_message_text.split("ID: `")[1].split("`")[0]
        user_id = int(user_id_str)

        await message.copy_to(chat_id=user_id, reply_markup=None)
        await message.reply("✅ تم إرسال الرد بنجاح للمستخدم.")

    except (IndexError, ValueError):
        await message.reply("❌ خطأ في استخراج ID المستخدم. تأكد من الرد على الرسالة الصحيحة.")
    except Exception as e:
        await message.reply(f"❌ فشل إرسال الرسالة: {e}")


# معالج رسائل المستخدمين العاديين
@dp.message_handler(lambda message: message.from_user.id != ADMIN_CHAT_ID, content_types=types.ContentTypes.ANY, state="*")
async def handle_user_message(message: types.Message):
    user_id = message.from_user.id
    if is_banned(user_id):
        return

    if is_spam(user_id):
        await message.reply("⚠️ لقد أرسلت رسائل كثيرة بسرعة. يرجى التمهل قليلاً.")
        return

    # التحقق من الردود التلقائية للرسائل النصية فقط
    if message.text and message.text.strip() in AUTO_REPLIES:
        await message.reply(AUTO_REPLIES[message.text.strip()], reply_markup=create_buttons())
        return

    # إرسال رسالة المستخدم إلى المدير
    try:
        header = (f"📩 رسالة جديدة من: {message.from_user.full_name}\n"
                  f"المعرف: @{message.from_user.username}\n"
                  f"ID: `{user_id}`")
        
        # إعادة توجيه الرسالة مع إضافة معلومات المستخدم
        await message.forward(ADMIN_CHAT_ID)
        await bot.send_message(ADMIN_CHAT_ID, header, parse_mode="Markdown")

        # إرسال رسالة تأكيد للمستخدم
        reply_text = bot_data.get("reply_message", "✅ تم استلام رسالتك بنجاح، سيتم الرد عليك قريباً.")
        await message.reply(reply_text, reply_markup=create_buttons())

    except Exception as e:
        print(f"❌ Error forwarding message from user {user_id}: {e}")
        await message.reply("حدث خطأ ما أثناء إرسال رسالتك. يرجى المحاولة مرة أخرى.")

# معالج الأزرار المضمنة للمستخدمين
@dp.callback_query_handler(lambda c: c.from_user.id != ADMIN_CHAT_ID, state="*")
async def process_user_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    data = callback_query.data
    response_text = ""

    if data == "hijri_today":
        response_text = get_hijri_date()
    elif data == "live_time":
        response_text = get_live_time()
    elif data == "daily_reminder":
        response_text = get_daily_reminder()
    elif data == "from_developer":
        response_text = "تم تطوير هذا البوت بواسطة [أبو سيف بن ذي يزن](https://t.me/HejriCalender) 👨‍💻"
    
    if response_text:
        await bot.send_message(callback_query.from_user.id, response_text, parse_mode="Markdown")

# معالج أزرار لوحة تحكم المدير
@dp.callback_query_handler(lambda c: c.from_user.id == ADMIN_CHAT_ID, state="*")
async def process_admin_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    data = callback_query.data

    if data == "close_panel":
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        return

    if data == "admin_stats":
        uptime = datetime.datetime.now() - start_time
        days, remainder = divmod(uptime.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)

        stats_text = (
            f"📊 **إحصائيات البوت**\n\n"
            f"👥 إجمالي المستخدمين: {len(USERS_LIST)}\n"
            f"🚫 المستخدمون المحظورون: {len(BANNED_USERS)}\n"
            f"📝 الردود التلقائية: {len(AUTO_REPLIES)}\n"
            f"💡 التذكيرات: {len(DAILY_REMINDERS)}\n"
            f"⏰ مدة التشغيل: {int(days)} يوم, {int(hours)} ساعة, {int(minutes)} دقيقة"
        )
        await bot.edit_message_text(stats_text, callback_query.message.chat.id, callback_query.message.message_id, reply_markup=create_admin_panel(), parse_mode="Markdown")

    # يمكنك إضافة المزيد من المنطق لأزرار المدير هنا
    # Example:
    elif data == "admin_ban":
        # Here you would typically ask for the user ID to ban
        # await state.set_state(AdminStates.waiting_for_ban_id)
        await bot.send_message(callback_query.from_user.id, "ميزة الحظر قيد التطوير.")
        
    # And so on for other buttons...


# ----------------- مهام الخلفية -----------------
async def keep_alive_ping():
    # The web server handles keeping the bot alive on Render.
    # This function can be used for periodic health checks.
    while True:
        await asyncio.sleep(1800)  # Sleep for 30 minutes
        try:
            me = await bot.get_me()
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Health check: Bot @{me.username} is alive.")
        except Exception as e:
            print(f"Health check failed: {e}")

# ----------------- التشغيل -----------------
async def on_startup(dp):
    print("-----------------------------------------")
    print("Bot is starting up...")
    # إرسال رسالة للمدير عند بدء التشغيل
    try:
        await bot.send_message(ADMIN_CHAT_ID, "✅ **البوت قيد التشغيل الآن!**", parse_mode="Markdown")
    except Exception as e:
        print(f"Could not send startup message to admin: {e}")
    
    # بدء مهام الخلفية
    asyncio.create_task(keep_alive_ping())

    print("Bot is now online and running.")
    print("-----------------------------------------")


if __name__ == "__main__":
    print("Attempting to start polling...")
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

 