import asyncio
import datetime
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
from utils.helpers import *
from utils.tasks import send_channel_message
from database import save_data

# --- دالة لوحة التحكم الرئيسية ---
async def admin_panel(message: types.Message):
    await message.reply("🔧 **لوحة التحكم الإدارية**\n\nأهلاً بك. اختر الإجراء المطلوب:", reply_markup=create_admin_panel())

# --- دالة رد المشرف على المستخدم ---
async def handle_admin_reply(message: types.Message):
    if not message.reply_to_message or not message.reply_to_message.forward_from:
        return

    user_id_to_reply = message.reply_to_message.forward_from.id
    original_user_message_id = user_threads.get(user_id_to_reply)

    try:
        await message.copy_to(chat_id=user_id_to_reply, reply_to_message_id=original_user_message_id)
        await message.reply("✅ **تم إرسال ردك للمستخدم بنجاح.**")
    except Exception as e:
        await message.reply(f"❌ **فشل إرسال الرد.**\nالخطأ: {e}")

# --- معالج الأزرار الرئيسي ---
async def process_admin_callback(cq: types.CallbackQuery, state: FSMContext):
    await cq.answer()
    await state.finish()
    data = cq.data
    
    menus = {
        "admin_replies": "📝 **إدارة الردود التلقائية**", "admin_reminders": "💭 **إدارة التذكيرات اليومية**",
        "admin_channel": "📢 **إدارة رسائل القناة**", "admin_ban": "🚫 **إدارة الحظر**",
        "admin_broadcast": f"📤 **النشر الجماعي** (لـ {len(USERS_LIST)} مستخدم)", "admin_channel_settings": "⚙️ **إعدادات القناة**",
        "admin_messages_settings": "💬 **إعدادات الرسائل**", "admin_media_settings": f"🔒 **إدارة الوسائط**",
        "admin_memory_management": "🧠 **إدارة الذاكرة**"
    }
    if data in menus:
        await cq.message.edit_text(f"{menus[data]}\n\nاختر الإجراء المطلوب:", reply_markup=get_menu_keyboard(data))
        return

    list_menus = {
        "show_replies": ("📝 **الردود الحالية:**", "admin_replies", [f"🔹 `{k}`" for k in AUTO_REPLIES.keys()]),
        "show_reminders": ("💭 **التذكيرات الحالية:**", "admin_reminders", [f"{i+1}. {r[:50]}..." for i, r in enumerate(DAILY_REMINDERS)]),
        "show_channel_msgs": ("📢 **رسائل القناة الحالية:**", "admin_channel", [f"{i+1}. {m[:50]}..." for i, m in enumerate(CHANNEL_MESSAGES)]),
        "show_banned": ("🚫 **المحظورون حالياً:**", "admin_ban", [f"`{uid}`" for uid in BANNED_USERS])
    }
    if data in list_menus:
        title, back_cb, items = list_menus[data]
        text = f"{title}\n\n" + ("\n".join(items) if items else "لا يوجد شيء لعرضه حالياً.")
        await cq.message.edit_text(text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text="🔙 العودة", callback_data=back_cb)))
        return

    prompts = {
        "add_reply": ("📝 أرسل الرد بالتنسيق:\n`الكلمة المفتاحية|نص الرد`", AdminStates.waiting_for_new_reply),
        "delete_reply_menu": ("🗑️ أرسل الكلمة المفتاحية للرد الذي تريد حذفه:", AdminStates.waiting_for_delete_reply),
        "add_reminder": ("💭 أرسل نص التذكير الجديد:", AdminStates.waiting_for_new_reminder),
        "delete_reminder_menu": ("🗑️ أرسل رقم التذكير الذي تريد حذفه:", AdminStates.waiting_for_delete_reminder),
        "add_channel_msg": ("➕ أرسل نص الرسالة الجديدة للقناة:", AdminStates.waiting_for_new_channel_message),
        "delete_channel_msg_menu": ("🗑️ أرسل رقم رسالة القناة التي تريد حذفها:", AdminStates.waiting_for_delete_channel_msg),
        "instant_channel_post": ("📤 أرسل الرسالة التي تريد نشرها الآن:", AdminStates.waiting_for_instant_channel_post),
        "ban_user": ("🚫 أرسل ID المستخدم الرقمي للحظر:", AdminStates.waiting_for_ban_id),
        "unban_user": ("✅ أرسل ID المستخدم الرقمي لإلغاء الحظر:", AdminStates.waiting_for_unban_id),
        "send_broadcast": ("📤 أرسل الرسالة الجماعية:", AdminStates.waiting_for_broadcast_message),
        "set_channel_id": ("🆔 أرسل ID القناة الجديد (مثال: `@username`):", AdminStates.waiting_for_channel_id),
        "set_schedule_time": ("⏰ أرسل الفترة بالساعات (مثال: `24`):", AdminStates.waiting_for_schedule_time),
        "set_welcome_msg": ("👋 أرسل نص الترحيب الجديد. استخدم `{name}` لاسم المستخدم:", AdminStates.waiting_for_welcome_message),
        "set_reply_msg": ("💬 أرسل نص الرد التلقائي الجديد:", AdminStates.waiting_for_reply_message),
        "set_media_reject_msg": ("✏️ أرسل نص رسالة رفض الوسائط الجديد:", AdminStates.waiting_for_media_reject_message),
        "clear_user_messages": ("🗑️ أرسل ID المستخدم لمسح بياناته المؤقتة:", AdminStates.waiting_for_clear_user_id),
    }
    if data in prompts:
        prompt_text, state_to_set = prompts[data]
        await state.set_state(state_to_set)
        await cq.message.edit_text(f"{prompt_text}\n\nلإلغاء العملية، أرسل /cancel.")
        return

    if data == "close_panel": await cq.message.delete()
    elif data == "back_to_main": await cq.message.edit_text("🔧 **لوحة التحكم الإدارية**", reply_markup=create_admin_panel())
    elif data == "admin_stats":
        stats = f"📊 **إحصائيات البوت**\n\n👥 المستخدمون: {len(USERS_LIST)}\n🚫 المحظورون: {len(BANNED_USERS)}\n📝 الردود: {len(AUTO_REPLIES)}\n💭 التذكيرات: {len(DAILY_REMINDERS)}\n📢 رسائل القناة: {len(CHANNEL_MESSAGES)}"
        await cq.message.edit_text(stats, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text="🔙 العودة", callback_data="back_to_main")))
    elif data == "deploy_status":
        uptime = datetime.datetime.now() - start_time
        status = f"🚀 **حالة النشر**\n\n✅ **الحالة:** نشط\n⏰ **مدة التشغيل:** {str(uptime).split('.')[0]}"
        await cq.message.edit_text(status, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text="🔙 العودة", callback_data="back_to_main")))
    elif data == "toggle_media":
        bot_data["allow_media"] = not bot_data.get("allow_media", False)
        save_data(bot_data)
        status = "✅ مسموح الآن" if bot_data["allow_media"] else "❌ ممنوع الآن"
        await cq.answer(f"تم تغيير حالة استقبال الوسائط إلى: {status}", show_alert=True)
        await cq.message.edit_text(f"🔒 **إدارة الوسائط**\n\n**الحالة الحالية:** {status}\n\nاختر الإجراء المطلوب:", reply_markup=get_menu_keyboard("admin_media_settings"))
    elif data == "clear_temp_memory":
        count = len(user_message_count) + len(silenced_users)
        user_message_count.clear(); silenced_users.clear()
        await cq.answer(f"✅ تم بنجاح مسح {count} سجل من ذاكرة الحماية.", show_alert=True)

def get_menu_keyboard(menu_type):
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons_map = {
        "admin_replies": [("➕ إضافة رد", "add_reply"), ("📝 عرض الردود", "show_replies"), ("🗑️ حذف رد", "delete_reply_menu")],
        "admin_reminders": [("➕ إضافة تذكير", "add_reminder"), ("📝 عرض التذكيرات", "show_reminders"), ("🗑️ حذف تذكير", "delete_reminder_menu")],
        "admin_channel": [("➕ إضافة رسالة", "add_channel_msg"), ("📝 عرض الرسائل", "show_channel_msgs"), ("🗑️ حذف رسالة", "delete_channel_msg_menu"), ("📤 نشر فوري", "instant_channel_post")],
        "admin_ban": [("🚫 حظر مستخدم", "ban_user"), ("✅ إلغاء حظر", "unban_user"), ("📋 قائمة المحظورين", "show_banned")],
        "admin_broadcast": [("📤 إرسال رسالة جماعية", "send_broadcast")],
        "admin_channel_settings": [("🆔 تعديل ID القناة", "set_channel_id"), ("⏰ تعديل فترة النشر", "set_schedule_time")],
        "admin_messages_settings": [("👋 تعديل رسالة الترحيب", "set_welcome_msg"), ("💬 تعديل رسالة الرد", "set_reply_msg")],
        "admin_media_settings": [("🔒 منع الوسائط" if bot_data.get('allow_media') else "🔓 السماح بالوسائط", "toggle_media"), ("✏️ تعديل رسالة الرفض", "set_media_reject_msg")],
        "admin_memory_management": [("🗑️ مسح بيانات مستخدم", "clear_user_messages"), ("🧹 مسح ذاكرة Spam", "clear_temp_memory")]
    }
    buttons = [InlineKeyboardButton(text=text, callback_data=cb) for text, cb in buttons_map.get(menu_type, [])]
    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton(text="🔙 العودة للوحة التحكم", callback_data="back_to_main"))
    return keyboard

# --- معالجات حالات FSM ---
async def cancel_state(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply("✅ تم إلغاء العملية بنجاح.", reply_markup=create_admin_panel())

async def process_text_input(m: types.Message, state: FSMContext, success_msg: str, data_key: str, data_list: list = None):
    text = m.text.strip()
    if data_list is not None: data_list.append(text)
    bot_data[data_key] = data_list if data_list is not None else text
    save_data(bot_data)
    await m.reply(success_msg.format(text=text), reply_markup=create_admin_panel())
    await state.finish()

async def process_new_reply(m: types.Message, state: FSMContext):
    try:
        trigger, response = map(str.strip, m.text.split('|', 1))
        AUTO_REPLIES[trigger] = response; bot_data["auto_replies"] = AUTO_REPLIES; save_data(bot_data)
        await m.reply(f"✅ **تم إضافة الرد بنجاح!**\n\n**عندما يقول المستخدم:** `{trigger}`\n**سيرد البوت:** {response}", reply_markup=create_admin_panel())
    except ValueError: await m.reply("❌ **تنسيق خاطئ!**\nالرجاء استخدام: `الكلمة المفتاحية|نص الرد`")
    await state.finish()

async def process_delete_reply(m: types.Message, state: FSMContext):
    trigger = m.text.strip()
    if trigger in AUTO_REPLIES:
        del AUTO_REPLIES[trigger]; bot_data["auto_replies"] = AUTO_REPLIES; save_data(bot_data)
        await m.reply(f"✅ تم حذف الرد الخاص بالكلمة `{trigger}` بنجاح.", reply_markup=create_admin_panel())
    else: await m.reply(f"❌ لم يتم العثور على رد للكلمة `{trigger}`.")
    await state.finish()

async def process_delete_by_index(m: types.Message, state: FSMContext, data_list: list, data_key: str, item_name: str):
    try:
        idx = int(m.text.strip()) - 1
        if 0 <= idx < len(data_list):
            removed = data_list.pop(idx); bot_data[data_key] = data_list; save_data(bot_data)
            await m.reply(f"✅ تم حذف {item_name}:\n`{removed}`", reply_markup=create_admin_panel())
        else: await m.reply(f"❌ رقم غير صالح. الرجاء إدخال رقم بين 1 و {len(data_list)}.")
    except ValueError: await m.reply("❌ الرجاء إرسال رقم صحيح.")
    await state.finish()

async def process_ban_unban(m: types.Message, state: FSMContext, ban_action: bool):
    try:
        user_id = int(m.text.strip())
        if ban_action:
            BANNED_USERS.add(user_id)
            await m.reply(f"🚫 تم حظر المستخدم `{user_id}` بنجاح.", reply_markup=create_admin_panel())
        else:
            if user_id in BANNED_USERS:
                BANNED_USERS.remove(user_id)
                await m.reply(f"✅ تم إلغاء حظر المستخدم `{user_id}` بنجاح.", reply_markup=create_admin_panel())
            else: await m.reply("❌ هذا المستخدم غير محظور أصلاً.")
        bot_data["banned_users"] = list(BANNED_USERS); save_data(bot_data)
    except ValueError: await m.reply("❌ الرجاء إرسال ID رقمي صحيح.")
    await state.finish()

async def process_broadcast(m: types.Message, state: FSMContext):
    success_count = 0; failed_count = 0
    for user_id in USERS_LIST:
        try:
            await m.copy_to(user_id); success_count += 1
            await asyncio.sleep(0.1)
        except: failed_count += 1
    await m.reply(f"✅ **اكتمل الإرسال الجماعي.**\n\n**النتائج:**\n- **نجح:** {success_count}\n- **فشل:** {failed_count}", reply_markup=create_admin_panel())
    await state.finish()

async def process_clear_user_id(m: types.Message, state: FSMContext):
    try:
        user_id = int(m.text.strip())
        count = 0
        if user_id in user_message_count: del user_message_count[user_id]; count += 1
        if user_id in silenced_users: del silenced_users[user_id]; count += 1
        await m.reply(f"✅ تم مسح {count} سجل من ذاكرة الحماية للمستخدم `{user_id}`.", reply_markup=create_admin_panel())
    except ValueError: await m.reply("❌ الرجاء إرسال ID رقمي صحيح.")
    await state.finish()
    
# --- تسجيل جميع المعالجات ---
def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(admin_panel, lambda m: m.from_user.id == ADMIN_CHAT_ID and m.text == "/admin", state="*")
    dp.register_message_handler(handle_admin_reply, lambda m: m.from_user.id == ADMIN_CHAT_ID and m.reply_to_message, content_types=types.ContentTypes.ANY, state="*")
    dp.register_callback_query_handler(process_admin_callback, lambda q: q.from_user.id == ADMIN_CHAT_ID, state="*")
    dp.register_message_handler(cancel_state, lambda m: m.from_user.id == ADMIN_CHAT_ID and m.text.lower() == '/cancel', state='*')
    
    # تسجيل معالجات FSM
    dp.register_message_handler(process_new_reply, state=AdminStates.waiting_for_new_reply)
    dp.register_message_handler(process_delete_reply, state=AdminStates.waiting_for_delete_reply)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, "✅ **تم إضافة التذكير بنجاح!**\n\nالنص: {text}", "daily_reminders", DAILY_REMINDERS), state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(lambda m, s: process_delete_by_index(m, s, DAILY_REMINDERS, "daily_reminders", "التذكير"), state=AdminStates.waiting_for_delete_reminder)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, "✅ **تم إضافة رسالة القناة بنجاح!**\n\nالنص: {text}", "channel_messages", CHANNEL_MESSAGES), state=AdminStates.waiting_for_new_channel_message)
    dp.register_message_handler(lambda m, s: process_delete_by_index(m, s, CHANNEL_MESSAGES, "channel_messages", "الرسالة"), state=AdminStates.waiting_for_delete_channel_msg)
    dp.register_message_handler(lambda m, s: send_channel_message(m.text.strip()), state=AdminStates.waiting_for_instant_channel_post)
    dp.register_message_handler(lambda m, s: process_ban_unban(m, s, ban_action=True), state=AdminStates.waiting_for_ban_id)
    dp.register_message_handler(lambda m, s: process_ban_unban(m, s, ban_action=False), state=AdminStates.waiting_for_unban_id)
    dp.register_message_handler(process_broadcast, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_broadcast_message)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, "✅ **تم تحديث ID القناة بنجاح إلى:** `{text}`", "channel_id"), state=AdminStates.waiting_for_channel_id)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, "✅ **تم تحديث رسالة الترحيب بنجاح.**", "welcome_message"), state=AdminStates.waiting_for_welcome_message)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, "✅ **تم تحديث رسالة الرد التلقائي بنجاح.**", "reply_message"), state=AdminStates.waiting_for_reply_message)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, "✅ **تم تحديث رسالة رفض الوسائط بنجاح.**", "media_reject_message"), state=AdminStates.waiting_for_media_reject_message)
    dp.register_message_handler(process_clear_user_id, state=AdminStates.waiting_for_clear_user_id)
    
    @dp.message_handler(state=AdminStates.waiting_for_schedule_time)
    async def process_schedule_time(m: types.Message, state: FSMContext):
        try:
            hours = float(m.text.strip())
            bot_data["schedule_interval_seconds"] = int(hours * 3600)
            save_data(bot_data)
            await m.reply(f"✅ **تم تحديث فترة النشر التلقائي إلى كل {hours} ساعة.**", reply_markup=create_admin_panel())
        except ValueError: await m.reply("❌ الرجاء إرسال رقم صحيح.")
        await state.finish()


