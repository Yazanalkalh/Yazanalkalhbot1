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
from aiogram.utils.exceptions import BotBlocked, ChatNotFound

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not API_TOKEN or not ADMIN_CHAT_ID:
    logging.critical("❌ خطأ: متغيرات البيئة BOT_TOKEN و ADMIN_CHAT_ID مطلوبة!")
    exit(1)

try:
    ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)
except ValueError:
    logging.critical("❌ خطأ: ADMIN_CHAT_ID يجب أن يكون رقماً صحيحاً")
    exit(1)

storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

start_time = datetime.datetime.now()

class AdminStates(StatesGroup):
    waiting_for_new_reply = State()
    waiting_for_delete_reply = State()
    waiting_for_new_reminder = State()
    waiting_for_delete_reminder = State()
    waiting_for_new_channel_message = State()
    waiting_for_delete_channel_msg = State()
    waiting_for_ban_id = State()
    waiting_for_unban_id = State()
    waiting_for_broadcast_message = State()
    waiting_for_channel_id = State()
    waiting_for_schedule_time = State()
    waiting_for_welcome_message = State()
    waiting_for_reply_message = State()
    waiting_for_media_reject_message = State()
    waiting_for_clear_user_id = State()


DATABASE_FILE = "bot_data.json"

def load_data():
    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "auto_replies": {}, "daily_reminders": [], "channel_messages": [],
            "banned_users": [], "users": [], "channel_id": CHANNEL_ID or "", "allow_media": False,
            "media_reject_message": "❌ يُسمح بالرسائل النصية فقط.",
            "rejected_media_count": 0, "welcome_message": "", "reply_message": "",
            "schedule_interval_seconds": 86400
        }
    except json.JSONDecodeError:
        logging.error(f"خطأ في قراءة ملف {DATABASE_FILE}.")
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

AUTO_REPLIES = bot_data.get("auto_replies", {})
DAILY_REMINDERS = bot_data.get("daily_reminders", [])
CHANNEL_MESSAGES = bot_data.get("channel_messages", [])

user_messages = {}
user_message_count = {}
silenced_users = {}

def is_banned(user_id):
    return user_id in BANNED_USERS

def check_spam_limit(user_id):
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
        return False, "limit_exceeded"
    return True, "allowed"

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
        hijri_months = {1: "محرم", 2: "صفر", 3: "ربيع الأول", 4: "ربيع الآخر", 5: "جمادى الأولى", 6: "جمادى الآخرة", 7: "رجب", 8: "شعبان", 9: "رمضان", 10: "شوال", 11: "ذو القعدة", 12: "ذو الحجة"}
        weekdays = {0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"}
        return f"🌙 التاريخ الهجري اليوم:\n📅 {hijri_date.day} {hijri_months[hijri_date.month]} {hijri_date.year} هـ\n📆 {weekdays[today.weekday()]}\n\n📅 التاريخ الميلادي:\n🗓️ {today.strftime('%d/%m/%Y')} م"
    except ImportError:
        return "🌙 لعرض التاريخ الهجري، يجب تثبيت مكتبة `hijri-converter`."
    except Exception as e:
        return f"🌙 عذراً، حدث خطأ: {e}"

def get_daily_reminder():
    return random.choice(DAILY_REMINDERS) if DAILY_REMINDERS else "لا توجد تذكيرات متاحة."

def get_live_time():
    try:
        import pytz
        now = datetime.datetime.now(pytz.timezone('Asia/Riyadh'))
    except ImportError:
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
    weekdays = {0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"}
    months = {1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"}
    return f"🕐 الساعة الآن: {now.strftime('%H:%M:%S')}\n📅 التاريخ: {weekdays[now.weekday()]} - {now.day} {months[now.month]} {now.year}\n🕌 بتوقيت مدينة الرياض"

async def schedule_channel_messages():
    await asyncio.sleep(10) # Initial delay
    while True:
        try:
            channel_id = bot_data.get("channel_id")
            if channel_id and CHANNEL_MESSAGES:
                message = random.choice(CHANNEL_MESSAGES)
                if not channel_id.startswith('@') and not channel_id.startswith('-'):
                    channel_id = '@' + channel_id
                await bot.send_message(channel_id, message)
                logging.info(f"✅ تم إرسال رسالة مجدولة للقناة: {channel_id}")
            
            interval = bot_data.get("schedule_interval_seconds", 86400)
            await asyncio.sleep(interval)
        except Exception as e:
            logging.error(f"❌ خطأ في جدولة الرسائل: {e}")
            await asyncio.sleep(60)

@dp.message_handler(lambda message: message.from_user.id == ADMIN_CHAT_ID and message.text == "/admin", state="*")
async def admin_panel(message: types.Message):
    await message.reply("🔧 **لوحة التحكم الإدارية**", reply_markup=create_admin_panel(), parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.from_user.id == ADMIN_CHAT_ID, state="*")
async def process_admin_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    data = callback_query.data
    msg = callback_query.message

    # Main Navigation
    if data == "back_to_main":
        await msg.edit_text("🔧 **لوحة التحكم الإدارية**", reply_markup=create_admin_panel(), parse_mode="Markdown")
    elif data == "close_panel":
        await msg.delete()

    # Sub-menus
    elif data == "admin_replies":
        kb = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton("➕ إضافة", callback_data="add_reply"), InlineKeyboardButton("📝 عرض", callback_data="show_replies"), InlineKeyboardButton("🗑️ حذف", callback_data="delete_reply"), InlineKeyboardButton("🔙 عودة", callback_data="back_to_main"))
        await msg.edit_text("📝 **إدارة الردود التلقائية**", reply_markup=kb)
    elif data == "admin_reminders":
        kb = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton("➕ إضافة", callback_data="add_reminder"), InlineKeyboardButton("📝 عرض", callback_data="show_reminders"), InlineKeyboardButton("🗑️ حذف", callback_data="delete_reminder"), InlineKeyboardButton("🔙 عودة", callback_data="back_to_main"))
        await msg.edit_text("💭 **إدارة التذكيرات اليومية**", reply_markup=kb)
    elif data == "admin_ban":
        kb = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton("🚫 حظر", callback_data="ban_user"), InlineKeyboardButton("✅ إلغاء الحظر", callback_data="unban_user"), InlineKeyboardButton("📋 عرض المحظورين", callback_data="show_banned"), InlineKeyboardButton("🔙 عودة", callback_data="back_to_main"))
        await msg.edit_text("🚫 **إدارة الحظر**", reply_markup=kb)
    
    # Actions that require state (FSM)
    elif data == "add_reply":
        await state.set_state(AdminStates.waiting_for_new_reply)
        await msg.edit_text("✍️ أرسل الرد الجديد بالصيغة التالية:\n`الكلمة المفتاحية >> نص الرد`", parse_mode="Markdown")
    elif data == "delete_reply":
        await state.set_state(AdminStates.waiting_for_delete_reply)
        await msg.edit_text("🗑️ أرسل الكلمة المفتاحية للرد الذي تريد حذفه:")
    elif data == "add_reminder":
        await state.set_state(AdminStates.waiting_for_new_reminder)
        await msg.edit_text("✍️ أرسل نص التذكير الجديد:")
    elif data == "delete_reminder":
        await state.set_state(AdminStates.waiting_for_delete_reminder)
        reminders_text = "🔢 أرسل رقم التذكير الذي تريد حذفه:\n\n" + "\n".join([f"{i+1}. {r[:50]}..." for i, r in enumerate(DAILY_REMINDERS)])
        await msg.edit_text(reminders_text)
    elif data == "ban_user":
        await state.set_state(AdminStates.waiting_for_ban_id)
        await msg.edit_text("🚫 أرسل ID المستخدم الذي تريد حظره:")
    elif data == "unban_user":
        await state.set_state(AdminStates.waiting_for_unban_id)
        await msg.edit_text("✅ أرسل ID المستخدم الذي تريد إلغاء حظره:")
    elif data == "admin_broadcast":
        await state.set_state(AdminStates.waiting_for_broadcast_message)
        await msg.edit_text("📤 أرسل الرسالة التي تريد بثها لجميع المستخدمين:")
    elif data == "admin_channel_settings":
        await state.set_state(AdminStates.waiting_for_channel_id)
        await msg.edit_text(f"⚙️ القناة الحالية: `{bot_data.get('channel_id')}`\n\nأرسل معرف القناة الجديد (مثال: `@channel_username` أو `-100123456789`).", parse_mode="Markdown")
        
    # Actions that display data
    elif data == "show_replies":
        text = "📝 **الردود الحالية:**\n\n" + ("\n".join([f"`{k}` -> {v}" for k, v in AUTO_REPLIES.items()]) or "لا توجد ردود.")
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 عودة", callback_data="admin_replies")), parse_mode="Markdown")
    elif data == "show_reminders":
        text = "💭 **التذكيرات الحالية:**\n\n" + ("\n".join([f"{i+1}. {r}" for i, r in enumerate(DAILY_REMINDERS)]) or "لا توجد تذكيرات.")
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 عودة", callback_data="admin_reminders")))
    elif data == "show_banned":
        text = "🚫 **قائمة المحظورين:**\n\n" + ("\n".join(map(str, BANNED_USERS)) or "لا يوجد محظورين.")
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 عودة", callback_data="admin_ban")))
    elif data == "admin_stats":
        uptime = datetime.datetime.now() - start_time
        text = (f"📊 **إحصائيات البوت**\n\n"
                f"⏰ مدة التشغيل: {str(uptime).split('.')[0]}\n"
                f"👥 المستخدمين: {len(USERS_LIST)}\n"
                f"🚫 المحظورين: {len(BANNED_USERS)}\n"
                f"📝 الردود: {len(AUTO_REPLIES)}\n"
                f"💭 التذكيرات: {len(DAILY_REMINDERS)}")
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 عودة", callback_data="back_to_main")))

# Handlers for FSM states
@dp.message_handler(state=AdminStates.waiting_for_new_reply)
async def process_new_reply(message: types.Message, state: FSMContext):
    if '>>' in message.text:
        trigger, response = map(str.strip, message.text.split('>>', 1))
        AUTO_REPLIES[trigger] = response
        bot_data['auto_replies'] = AUTO_REPLIES
        save_data(bot_data)
        await message.reply(f"✅ تم إضافة الرد بنجاح.\n`{trigger}` -> `{response}`", parse_mode="Markdown")
    else:
        await message.reply("❌ صيغة خاطئة. يرجى استخدام: `الكلمة >> الرد`")
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_delete_reply)
async def process_delete_reply(message: types.Message, state: FSMContext):
    trigger = message.text.strip()
    if trigger in AUTO_REPLIES:
        del AUTO_REPLIES[trigger]
        bot_data['auto_replies'] = AUTO_REPLIES
        save_data(bot_data)
        await message.reply(f"✅ تم حذف الرد `{trigger}` بنجاح.")
    else:
        await message.reply("❌ لم يتم العثور على هذه الكلمة المفتاحية.")
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_new_reminder)
async def process_new_reminder(message: types.Message, state: FSMContext):
    DAILY_REMINDERS.append(message.text.strip())
    bot_data['daily_reminders'] = DAILY_REMINDERS
    save_data(bot_data)
    await message.reply("✅ تم إضافة التذكير بنجاح.")
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_delete_reminder)
async def process_delete_reminder(message: types.Message, state: FSMContext):
    try:
        index = int(message.text.strip()) - 1
        if 0 <= index < len(DAILY_REMINDERS):
            removed = DAILY_REMINDERS.pop(index)
            bot_data['daily_reminders'] = DAILY_REMINDERS
            save_data(bot_data)
            await message.reply(f"✅ تم حذف التذكير: '{removed[:30]}...'")
        else:
            await message.reply("❌ رقم غير صالح.")
    except ValueError:
        await message.reply("❌ يرجى إرسال رقم فقط.")
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_ban_id)
async def process_ban_user(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
        BANNED_USERS.add(user_id)
        bot_data['banned_users'] = list(BANNED_USERS)
        save_data(bot_data)
        await message.reply(f"🚫 تم حظر المستخدم `{user_id}` بنجاح.")
    except ValueError:
        await message.reply("❌ ID غير صالح. يرجى إرسال أرقام فقط.")
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_unban_id)
async def process_unban_user(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
        BANNED_USERS.discard(user_id)
        bot_data['banned_users'] = list(BANNED_USERS)
        save_data(bot_data)
        await message.reply(f"✅ تم إلغاء حظر المستخدم `{user_id}`.")
    except ValueError:
        await message.reply("❌ ID غير صالح. يرجى إرسال أرقام فقط.")
    await state.finish()
    
@dp.message_handler(state=AdminStates.waiting_for_broadcast_message, content_types=types.ContentTypes.ANY)
async def process_broadcast(message: types.Message, state: FSMContext):
    await state.finish()
    sent_count = 0
    failed_count = 0
    status_msg = await message.reply("📤 جارِ بث الرسالة...")
    for user_id in list(USERS_LIST):
        try:
            await message.copy_to(user_id)
            sent_count += 1
            await asyncio.sleep(0.1)
        except (BotBlocked, ChatNotFound):
            failed_count += 1
            USERS_LIST.remove(user_id)
        except Exception:
            failed_count += 1
    
    bot_data['users'] = list(USERS_LIST)
    save_data(bot_data)
    await status_msg.edit_text(f"✅ تم إكمال البث.\n\n"
                               f"📤 تم الإرسال إلى: {sent_count} مستخدم\n"
                               f"❌ فشل الإرسال إلى: {failed_count} مستخدم")

@dp.message_handler(state=AdminStates.waiting_for_channel_id)
async def process_channel_id(message: types.Message, state: FSMContext):
    channel_id = message.text.strip()
    bot_data['channel_id'] = channel_id
    save_data(bot_data)
    await message.reply(f"✅ تم تحديث معرف القناة إلى: `{channel_id}`", parse_mode="Markdown")
    await state.finish()

@dp.message_handler(lambda message: message.from_user.id != ADMIN_CHAT_ID, content_types=types.ContentTypes.ANY, state="*")
async def handle_any_message(message: types.Message):
    user_id = message.from_user.id
    if is_banned(user_id): return

    is_spam, status = check_spam_limit(user_id)
    if not is_spam:
        await message.reply("⚠️ لقد تجاوزت حد الرسائل. يرجى الانتظار قليلاً.")
        return

    if user_id not in USERS_LIST:
        USERS_LIST.add(user_id)
        bot_data["users"] = list(USERS_LIST)
        save_data(bot_data)
        logging.info(f"مستخدم جديد: {message.from_user.full_name} ({user_id}).")

    if message.content_type == types.ContentType.TEXT:
        if message.text.strip().lower() in AUTO_REPLIES:
            await message.reply(AUTO_REPLIES[message.text.strip().lower()], reply_markup=create_buttons())
            return
        await message.reply(bot_data.get("reply_message") or "🌿 تم استلام رسالتك، شكراً لتواصلك.", reply_markup=create_buttons())
    elif not bot_data.get("allow_media", False):
        await message.reply(bot_data.get("media_reject_message", "❌ الوسائط غير مسموحة."))
        return
        
    try:
        fwd_msg = await message.forward(ADMIN_CHAT_ID)
        admin_text = f"📩 من: {message.from_user.full_name} (`{user_id}`)"
        info_msg = await bot.send_message(ADMIN_CHAT_ID, admin_text, reply_to_message_id=fwd_msg.message_id, parse_mode="Markdown")
        user_messages[info_msg.message_id] = {"user_id": user_id}
    except Exception as e:
        logging.error(f"خطأ في توجيه الرسالة: {e}")

@dp.message_handler(lambda msg: msg.from_user.id == ADMIN_CHAT_ID and msg.reply_to_message, content_types=types.ContentTypes.ANY, state="*")
async def handle_admin_reply(message: types.Message):
    user_info = user_messages.get(message.reply_to_message.message_id)
    if not user_info and message.reply_to_message.forward_from:
        user_id = message.reply_to_message.forward_from.id
    elif user_info:
        user_id = user_info['user_id']
    else:
        await message.reply("⚠️ لم يتم العثور على المستخدم الأصلي لهذه الرسالة.")
        return

    try:
        await message.copy_to(user_id)
        await message.reply("✅ تم إرسال الرد بنجاح.")
    except Exception as e:
        await message.reply(f"❌ فشل إرسال الرد: {e}")

@dp.callback_query_handler(lambda c: c.from_user.id != ADMIN_CHAT_ID, state="*")
async def process_user_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
    user_id = callback_query.from_user.id
    if is_banned(user_id): return
    
    actions = {
        "hijri_today": get_hijri_date,
        "live_time": get_live_time,
        "daily_reminder": get_daily_reminder,
    }
    
    if callback_query.data in actions:
        await bot.send_message(user_id, actions[callback_query.data]())
    elif callback_query.data == "from_developer":
        await bot.send_message(user_id, "تم تطوير هذا البوت بواسطة ✨ ابو سيف بن ذي يزن ✨\n[فريق التقويم الهجري](https://t.me/HejriCalender)", parse_mode="Markdown")

@dp.message_handler(commands=['start'], state="*")
async def send_welcome(message: types.Message):
    if is_banned(message.from_user.id): return
    welcome_text = bot_data.get("welcome_message") or (f"👋 أهلًا بك، {message.from_user.first_name}!\n"
                                                       "هذا البوت مخصص للتواصل مع إدارة القناة.")
    await message.reply(welcome_text.replace("{name}", message.from_user.first_name), reply_markup=create_buttons())

async def on_startup(dp):
    asyncio.create_task(schedule_channel_messages())
    logging.info("✅ البوت يعمل الآن!")
    await bot.send_message(ADMIN_CHAT_ID, "✅ **البوت يعمل الآن!**", parse_mode="Markdown")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)


