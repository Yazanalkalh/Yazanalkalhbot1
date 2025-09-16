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
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, CantParseEntities

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not API_TOKEN or not ADMIN_CHAT_ID:
    logger.critical("❌ FATAL: BOT_TOKEN and ADMIN_CHAT_ID environment variables are required!")
    exit(1)
try:
    ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)
except ValueError:
    logger.critical("❌ FATAL: ADMIN_CHAT_ID must be a valid integer.")
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

DATABASE_FILE = os.getenv("DATA_PATH", "bot_data.json")

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
        logger.error(f"Could not decode JSON from {DATABASE_FILE}. Starting with empty data.")
        return {}

def save_data(data):
    try:
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save data: {e}")

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
        return False
    user_data = user_message_count.setdefault(user_id, {"count": 0, "last_reset": current_time})
    if (current_time - user_data["last_reset"]).total_seconds() > 60:
        user_data["count"] = 0
        user_data["last_reset"] = current_time
    user_data["count"] += 1
    if user_data["count"] > 5:
        silenced_users[user_id] = current_time
        return False
    return True

def create_admin_panel():
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("📝 الردود", callback_data="admin_replies"),
        InlineKeyboardButton("💭 التذكيرات", callback_data="admin_reminders"),
        InlineKeyboardButton("📢 رسائل القناة", callback_data="admin_channel"),
        InlineKeyboardButton("🚫 الحظر", callback_data="admin_ban"),
        InlineKeyboardButton("📤 بث", callback_data="admin_broadcast"),
        InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
        InlineKeyboardButton("⚙️ إعدادات القناة", callback_data="admin_channel_settings"),
        InlineKeyboardButton("💬 إعدادات الرسائل", callback_data="admin_messages_settings"),
        InlineKeyboardButton("🔒 إدارة الوسائط", callback_data="admin_media_settings"),
        InlineKeyboardButton("🧠 الذاكرة", callback_data="admin_memory_management"),
        InlineKeyboardButton("❌ إغلاق", callback_data="close_panel")
    )

def create_buttons():
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("اليوم هجري", callback_data="hijri_today"),
        InlineKeyboardButton("🕐 الساعة والتاريخ", callback_data="live_time"),
        InlineKeyboardButton("تذكير يومي", callback_data="daily_reminder"),
        InlineKeyboardButton("من المطور", callback_data="from_developer")
    )

def get_hijri_date():
    try:
        from hijri_converter import convert
        today = datetime.date.today()
        h_date = convert.Gregorian(today.year, today.month, today.day).to_hijri()
        h_months = ["محرم", "صفر", "ربيع الأول", "ربيع الآخر", "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة"]
        wdays = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
        return f"📅 {h_date.day} {h_months[h_date.month-1]} {h_date.year} هـ\n📆 {wdays[today.weekday()]}"
    except ImportError:
        return "مكتبة `hijri-converter` غير مثبتة."
    except Exception as e:
        return f"حدث خطأ: {e}"

def get_daily_reminder():
    return random.choice(DAILY_REMINDERS) if DAILY_REMINDERS else "لا توجد تذكيرات."

async def schedule_channel_messages():
    await asyncio.sleep(15)
    while True:
        try:
            channel_id = bot_data.get("channel_id")
            if channel_id and CHANNEL_MESSAGES:
                message = random.choice(CHANNEL_MESSAGES)
                await bot.send_message(channel_id, message)
            await asyncio.sleep(bot_data.get("schedule_interval_seconds", 86400))
        except Exception as e:
            logger.error(f"Schedule Error: {e}")
            await asyncio.sleep(60)

@dp.message_handler(lambda m: m.from_user.id == ADMIN_CHAT_ID and m.text == "/admin", state="*")
async def admin_panel(message: types.Message):
    await message.reply("🔧 **لوحة التحكم**", reply_markup=create_admin_panel(), parse_mode="Markdown")

# --- ADMIN CALLBACK HANDLER ---
@dp.callback_query_handler(lambda c: c.from_user.id == ADMIN_CHAT_ID, state="*")
async def process_admin_callback(cq: types.CallbackQuery, state: FSMContext):
    await cq.answer()
    data = cq.data
    msg = cq.message

    # --- MENUS ---
    if data == "back_to_main":
        await msg.edit_text("🔧 **لوحة التحكم**", reply_markup=create_admin_panel(), parse_mode="Markdown")
    elif data == "close_panel": await msg.delete()
    elif data == "admin_replies":
        kb = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton("➕ إضافة", callback_data="add_reply"), InlineKeyboardButton("📝 عرض", callback_data="show_replies"), InlineKeyboardButton("🗑️ حذف", callback_data="delete_reply"), InlineKeyboardButton("🔙 عودة", callback_data="back_to_main"))
        await msg.edit_text("📝 **إدارة الردود**", reply_markup=kb)
    elif data == "admin_reminders":
        kb = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton("➕ إضافة", callback_data="add_reminder"), InlineKeyboardButton("📝 عرض", callback_data="show_reminders"), InlineKeyboardButton("🗑️ حذف", callback_data="delete_reminder"), InlineKeyboardButton("🔙 عودة", callback_data="back_to_main"))
        await msg.edit_text("💭 **إدارة التذكيرات**", reply_markup=kb)
    elif data == "admin_channel":
        kb = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton("➕ إضافة", callback_data="add_channel_msg"), InlineKeyboardButton("📝 عرض", callback_data="show_channel_msgs"), InlineKeyboardButton("🗑️ حذف", callback_data="delete_channel_msg"), InlineKeyboardButton("📤 نشر فوري", callback_data="instant_post"), InlineKeyboardButton("🔙 عودة", callback_data="back_to_main"))
        await msg.edit_text("📢 **إدارة رسائل القناة**", reply_markup=kb)
    elif data == "admin_ban":
        kb = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton("🚫 حظر", callback_data="ban_user"), InlineKeyboardButton("✅ إلغاء", callback_data="unban_user"), InlineKeyboardButton("📋 عرض", callback_data="show_banned"), InlineKeyboardButton("🔙 عودة", callback_data="back_to_main"))
        await msg.edit_text("🚫 **إدارة الحظر**", reply_markup=kb)
    elif data == "admin_channel_settings":
        interval_h = bot_data.get('schedule_interval_seconds', 86400) // 3600
        text = f"⚙️ **إعدادات القناة**\n\n- المعرف الحالي: `{bot_data.get('channel_id')}`\n- فترة النشر: كل {interval_h} ساعة"
        kb = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton("🆔 تعديل المعرف", callback_data="set_channel_id"), InlineKeyboardButton("⏰ تعديل الفترة", callback_data="set_schedule_time"), InlineKeyboardButton("🔙 عودة", callback_data="back_to_main"))
        await msg.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    elif data == "admin_messages_settings":
        kb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton("👋 تعديل رسالة الترحيب", callback_data="set_welcome_msg"), InlineKeyboardButton("💬 تعديل رسالة الرد", callback_data="set_reply_msg"), InlineKeyboardButton("🔙 عودة", callback_data="back_to_main"))
        await msg.edit_text("💬 **إعدادات الرسائل**", reply_markup=kb)
    elif data == "admin_media_settings":
        status = "✅ مسموح" if bot_data.get("allow_media") else "❌ محظور"
        text = f"🔒 **إدارة الوسائط**\n\n- الحالة: {status}\n- رسالة الرفض: `{bot_data.get('media_reject_message')}`"
        kb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(f"🔄 تبديل السماح (الوضع الحالي: {status})", callback_data="toggle_media"), InlineKeyboardButton("✏️ تعديل رسالة الرفض", callback_data="set_media_reject_msg"), InlineKeyboardButton("🔙 عودة", callback_data="back_to_main"))
        await msg.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    elif data == "admin_memory_management":
        kb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton("🧹 مسح ذاكرة Spam", callback_data="clear_spam_cache"), InlineKeyboardButton("🗑️ مسح بيانات مستخدم", callback_data="clear_user_data"), InlineKeyboardButton("🔙 عودة", callback_data="back_to_main"))
        await msg.edit_text(f"🧠 **إدارة الذاكرة**\n\n- المحادثات النشطة: {len(user_messages)}\n- إحصائيات Spam: {len(user_message_count)}", reply_markup=kb)

    # --- ACTIONS ---
    elif data == "add_reply": await state.set_state(AdminStates.waiting_for_new_reply); await msg.edit_text("✍️ أرسل الرد: `الكلمة >> نص الرد`", parse_mode="Markdown")
    elif data == "delete_reply": await state.set_state(AdminStates.waiting_for_delete_reply); await msg.edit_text("🗑️ أرسل الكلمة المفتاحية للحذف:")
    elif data == "add_reminder": await state.set_state(AdminStates.waiting_for_new_reminder); await msg.edit_text("✍️ أرسل نص التذكير الجديد:")
    elif data == "delete_reminder": await state.set_state(AdminStates.waiting_for_delete_reminder); await msg.edit_text("🔢 أرسل رقم التذكير للحذف:\n\n" + "\n".join([f"{i+1}. {r[:50]}" for i, r in enumerate(DAILY_REMINDERS)]))
    elif data == "add_channel_msg": await state.set_state(AdminStates.waiting_for_new_channel_message); await msg.edit_text("✍️ أرسل نص الرسالة الجديدة للقناة:")
    elif data == "delete_channel_msg": await state.set_state(AdminStates.waiting_for_delete_channel_msg); await msg.edit_text("🔢 أرسل رقم الرسالة للحذف:\n\n" + "\n".join([f"{i+1}. {r[:50]}" for i, r in enumerate(CHANNEL_MESSAGES)]))
    elif data == "ban_user": await state.set_state(AdminStates.waiting_for_ban_id); await msg.edit_text("🚫 أرسل ID المستخدم للحظر:")
    elif data == "unban_user": await state.set_state(AdminStates.waiting_for_unban_id); await msg.edit_text("✅ أرسل ID المستخدم لإلغاء الحظر:")
    elif data == "set_channel_id": await state.set_state(AdminStates.waiting_for_channel_id); await msg.edit_text("🆔 أرسل معرف القناة الجديد (username@ أو -100...):")
    elif data == "set_schedule_time": await state.set_state(AdminStates.waiting_for_schedule_time); await msg.edit_text("⏰ أرسل فترة النشر الجديدة (بالساعات):")
    elif data == "set_welcome_msg": await state.set_state(AdminStates.waiting_for_welcome_message); await msg.edit_text(f"👋 أرسل رسالة الترحيب الجديدة. استخدم `{{name}}` لاسم المستخدم.\n\nالحالية: `{bot_data.get('welcome_message')}`", parse_mode="Markdown")
    elif data == "set_reply_msg": await state.set_state(AdminStates.waiting_for_reply_message); await msg.edit_text(f"💬 أرسل رسالة الرد التلقائي الجديدة.\n\nالحالية: `{bot_data.get('reply_message')}`", parse_mode="Markdown")
    elif data == "set_media_reject_msg": await state.set_state(AdminStates.waiting_for_media_reject_message); await msg.edit_text(f"✏️ أرسل رسالة رفض الوسائط الجديدة.\n\nالحالية: `{bot_data.get('media_reject_message')}`", parse_mode="Markdown")
    elif data == "admin_broadcast": await state.set_state(AdminStates.waiting_for_broadcast_message); await msg.edit_text("📤 أرسل الرسالة للبث لجميع المستخدمين:")
    elif data == "clear_user_data": await state.set_state(AdminStates.waiting_for_clear_user_id); await msg.edit_text("🗑️ أرسل ID المستخدم لمسح بياناته:")
    elif data == "instant_post":
        if CHANNEL_MESSAGES: await bot.send_message(bot_data.get('channel_id'), random.choice(CHANNEL_MESSAGES)); await cq.message.reply("✅ تم نشر رسالة عشوائية.")
        else: await cq.message.reply("❌ لا توجد رسائل للنشر.")
    elif data == "toggle_media":
        bot_data["allow_media"] = not bot_data.get("allow_media", False)
        save_data(bot_data)
        await process_admin_callback(cq, state) # Refresh menu
    elif data == "clear_spam_cache":
        user_message_count.clear(); silenced_users.clear()
        await msg.reply("✅ تم مسح ذاكرة Spam المؤقتة.")
    elif data == "show_replies": await msg.edit_text("📝 **الردود:**\n" + ("\n".join(f"`{k}`: {v}" for k, v in AUTO_REPLIES.items()) or "لا يوجد"), reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 عودة", callback_data="admin_replies")), parse_mode="Markdown")
    elif data == "show_reminders": await msg.edit_text("💭 **التذكيرات:**\n" + ("\n".join(f"{i+1}. {r}" for i, r in enumerate(DAILY_REMINDERS)) or "لا يوجد"), reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 عودة", callback_data="admin_reminders")))
    elif data == "show_channel_msgs": await msg.edit_text("📢 **رسائل القناة:**\n" + ("\n".join(f"{i+1}. {r}" for i, r in enumerate(CHANNEL_MESSAGES)) or "لا يوجد"), reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 عودة", callback_data="admin_channel")))
    elif data == "show_banned": await msg.edit_text("🚫 **المحظورين:**\n" + ("\n".join(map(str, BANNED_USERS)) or "لا يوجد"), reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 عودة", callback_data="admin_ban")))
    elif data == "admin_stats":
        uptime = str(datetime.datetime.now() - start_time).split('.')[0]
        text = f"📊 **الإحصائيات**\n\n- التشغيل: {uptime}\n- المستخدمين: {len(USERS_LIST)}\n- المحظورين: {len(BANNED_USERS)}\n- الردود: {len(AUTO_REPLIES)}"
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 عودة", callback_data="back_to_main")))

# --- FSM HANDLERS ---
async def simple_text_save(message: types.Message, state: FSMContext, key: str, confirmation: str, list_mode=False):
    text = message.text.strip()
    if list_mode:
        bot_data.get(key, []).append(text)
    else:
        bot_data[key] = text
    save_data(bot_data)
    if key == 'auto_replies': AUTO_REPLIES.clear(); AUTO_REPLIES.update(bot_data['auto_replies'])
    elif key == 'daily_reminders': DAILY_REMINDERS.clear(); DAILY_REMINDERS.extend(bot_data['daily_reminders'])
    elif key == 'channel_messages': CHANNEL_MESSAGES.clear(); CHANNEL_MESSAGES.extend(bot_data['channel_messages'])
    await message.reply(confirmation)
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_new_reply)
async def process_new_reply(m: types.Message, state: FSMContext):
    if '>>' in m.text:
        trigger, response = map(str.strip, m.text.split('>>', 1))
        AUTO_REPLIES[trigger.lower()] = response
        bot_data['auto_replies'] = AUTO_REPLIES
        await simple_text_save(m, state, 'auto_replies', f"✅ تم إضافة الرد: `{trigger}`", list_mode=False)
    else: await m.reply("❌ صيغة خاطئة."); await state.finish()
@dp.message_handler(state=AdminStates.waiting_for_delete_reply)
async def process_delete_reply(m: types.Message, state: FSMContext):
    trigger = m.text.strip().lower()
    if trigger in AUTO_REPLIES:
        del AUTO_REPLIES[trigger]
        bot_data['auto_replies'] = AUTO_REPLIES
        save_data(bot_data); await m.reply(f"✅ تم حذف `{trigger}`.")
    else: await m.reply("❌ لم يتم العثور عليه.")
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_new_reminder)
async def process_new_reminder(m: types.Message, state: FSMContext): await simple_text_save(m, state, 'daily_reminders', "✅ تم إضافة التذكير.", list_mode=True)
@dp.message_handler(state=AdminStates.waiting_for_new_channel_message)
async def process_new_channel_msg(m: types.Message, state: FSMContext): await simple_text_save(m, state, 'channel_messages', "✅ تم إضافة رسالة القناة.", list_mode=True)
@dp.message_handler(state=AdminStates.waiting_for_welcome_message)
async def process_welcome_msg(m: types.Message, state: FSMContext): await simple_text_save(m, state, 'welcome_message', "✅ تم تحديث رسالة الترحيب.")
@dp.message_handler(state=AdminStates.waiting_for_reply_message)
async def process_reply_msg(m: types.Message, state: FSMContext): await simple_text_save(m, state, 'reply_message', "✅ تم تحديث رسالة الرد.")
@dp.message_handler(state=AdminStates.waiting_for_media_reject_message)
async def process_reject_msg(m: types.Message, state: FSMContext): await simple_text_save(m, state, 'media_reject_message', "✅ تم تحديث رسالة الرفض.")
@dp.message_handler(state=AdminStates.waiting_for_channel_id)
async def process_channel_id(m: types.Message, state: FSMContext): await simple_text_save(m, state, 'channel_id', f"✅ تم تحديث معرف القناة إلى: `{m.text.strip()}`",)

async def delete_by_index(message, state, data_list_key, confirmation):
    try:
        idx = int(message.text.strip()) - 1
        data_list = globals()[data_list_key]
        if 0 <= idx < len(data_list):
            data_list.pop(idx); bot_data[data_list_key.lower()] = data_list
            save_data(bot_data); await message.reply(confirmation)
        else: await message.reply("❌ رقم غير صالح.")
    except (ValueError, IndexError): await message.reply("❌ إدخال غير صالح.")
    await state.finish()
@dp.message_handler(state=AdminStates.waiting_for_delete_reminder)
async def process_delete_reminder(m: types.Message, state: FSMContext): await delete_by_index(m, state, 'DAILY_REMINDERS', "✅ تم حذف التذكير.")
@dp.message_handler(state=AdminStates.waiting_for_delete_channel_msg)
async def process_delete_channel_msg(m: types.Message, state: FSMContext): await delete_by_index(m, state, 'CHANNEL_MESSAGES', "✅ تم حذف الرسالة.")

@dp.message_handler(state=[AdminStates.waiting_for_ban_id, AdminStates.waiting_for_unban_id, AdminStates.waiting_for_clear_user_id])
async def process_user_id_actions(m: types.Message, state: FSMContext):
    try:
        user_id = int(m.text.strip())
        current_state = await state.get_state()
        if current_state == AdminStates.waiting_for_ban_id:
            BANNED_USERS.add(user_id); bot_data['banned_users'] = list(BANNED_USERS); save_data(bot_data)
            await m.reply(f"🚫 تم حظر `{user_id}`.")
        elif current_state == AdminStates.waiting_for_unban_id:
            BANNED_USERS.discard(user_id); bot_data['banned_users'] = list(BANNED_USERS); save_data(bot_data)
            await m.reply(f"✅ تم إلغاء حظر `{user_id}`.")
        elif current_state == AdminStates.waiting_for_clear_user_id:
            USERS_LIST.discard(user_id); bot_data['users'] = list(USERS_LIST); save_data(bot_data)
            await m.reply(f"🗑️ تم حذف بيانات المستخدم `{user_id}`.")
    except ValueError: await m.reply("❌ ID غير صالح.")
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_schedule_time)
async def process_schedule_time(m: types.Message, state: FSMContext):
    try:
        hours = int(m.text.strip())
        bot_data['schedule_interval_seconds'] = hours * 3600
        save_data(bot_data)
        await m.reply(f"✅ تم تحديث فترة النشر إلى كل {hours} ساعة.")
    except ValueError: await m.reply("❌ يرجى إرسال رقم صحيح.")
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_broadcast_message, content_types=types.ContentTypes.ANY)
async def process_broadcast(m: types.Message, state: FSMContext):
    await state.finish()
    status_msg = await m.reply("📤 جارِ البث..."); sent, failed = 0, 0
    for user_id in list(USERS_LIST):
        try: await m.copy_to(user_id); sent += 1; await asyncio.sleep(0.1)
        except (BotBlocked, ChatNotFound): failed += 1; USERS_LIST.remove(user_id)
        except Exception: failed += 1
    bot_data['users'] = list(USERS_LIST); save_data(bot_data)
    await status_msg.edit_text(f"✅ اكتمل البث.\n\n- أرسل إلى: {sent}\n- فشل لـ: {failed}")

# --- USER HANDLERS ---
@dp.message_handler(lambda m: m.from_user.id != ADMIN_CHAT_ID, content_types=types.ContentTypes.ANY, state="*")
async def handle_user_message(message: types.Message):
    user_id = message.from_user.id
    if is_banned(user_id) or not check_spam_limit(user_id): return

    if user_id not in USERS_LIST:
        USERS_LIST.add(user_id); bot_data["users"] = list(USERS_LIST); save_data(bot_data)
        logger.info(f"New user: {message.from_user.full_name} ({user_id})")

    if message.content_type == types.ContentType.TEXT:
        text_lower = message.text.strip().lower()
        if text_lower in AUTO_REPLIES:
            return await message.reply(AUTO_REPLIES[text_lower], reply_markup=create_buttons())
        reply_msg = bot_data.get("reply_message") or "🌿 شكراً لتواصلك."
        await message.reply(reply_msg, reply_markup=create_buttons())
    elif not bot_data.get("allow_media"):
        return await message.reply(bot_data.get("media_reject_message"))

    try:
        fwd_msg = await message.forward(ADMIN_CHAT_ID)
        info_msg = await bot.send_message(ADMIN_CHAT_ID, f"📩 من: {message.from_user.full_name} (`{user_id}`)", reply_to_message_id=fwd_msg.message_id, parse_mode="Markdown")
        user_messages[info_msg.message_id] = {"user_id": user_id}
    except Exception as e:
        logger.error(f"Forwarding Error: {e}")

@dp.message_handler(lambda m: m.from_user.id == ADMIN_CHAT_ID and m.reply_to_message, content_types=types.ContentTypes.ANY, state="*")
async def handle_admin_reply(m: types.Message):
    user_id = None
    if m.reply_to_message.forward_from:
        user_id = m.reply_to_message.forward_from.id
    else:
        info = user_messages.get(m.reply_to_message.message_id)
        if info: user_id = info['user_id']
    
    if user_id:
        try: await m.copy_to(user_id); await m.reply("✅ تم الإرسال.")
        except Exception as e: await m.reply(f"❌ فشل الإرسال: {e}")
    else: await m.reply("⚠️ لم يتم العثور على المستخدم الأصلي.")

@dp.callback_query_handler(lambda c: c.from_user.id != ADMIN_CHAT_ID, state="*")
async def process_user_callback(cq: types.CallbackQuery):
    await cq.answer()
    if is_banned(cq.from_user.id): return
    actions = {"hijri_today": get_hijri_date, "live_time": get_daily_reminder}
    if cq.data in actions:
        await cq.message.answer(actions[cq.data]())
    elif cq.data == "from_developer":
        await cq.message.answer("✨ ابو سيف بن ذي يزن ✨\n[t.me/HejriCalender](https://t.me/HejriCalender)", parse_mode="Markdown")

@dp.message_handler(commands=['start'], state="*")
async def send_welcome(m: types.Message):
    if is_banned(m.from_user.id): return
    name = m.from_user.first_name
    welcome_text = (bot_data.get("welcome_message") or "👋 أهلًا بك، {name}!\nهذا بوت للتواصل.").replace("{name}", name)
    await m.reply(welcome_text, reply_markup=create_buttons())

async def on_startup(dp):
    asyncio.create_task(schedule_channel_messages())
    await bot.send_message(ADMIN_CHAT_ID, "✅ **البوت يعمل الآن!**", parse_mode="Markdown")
    logger.info("Bot started successfully.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)


