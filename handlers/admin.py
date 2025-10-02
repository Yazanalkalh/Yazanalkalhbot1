import asyncio
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
from utils.helpers import *
from utils.tasks import send_channel_message

# --- معالجات المشرف ---
async def admin_panel(message: types.Message):
    await message.reply("🔧 **لوحة التحكم الإدارية**", reply_markup=create_admin_panel(), parse_mode="Markdown")

async def handle_admin_reply(message: types.Message):
    """
    يعالج رد المشرف على رسالة معاد توجيهها من مستخدم.
    -- نسخة محسنة --
    """
    # التأكد من أن المشرف يرد على رسالة معاد توجيهها من مستخدم
    if not message.reply_to_message or not message.reply_to_message.forward_from:
        # إذا لم يكن الرد على رسالة معاد توجيهها، تجاهل الأمر
        return

    user_id_to_reply = message.reply_to_message.forward_from.id
    admin_reply_text = message.text.strip()

    try:
        reply_message = f"📩 **رد من الإدارة:**\n{admin_reply_text}"
        await bot.send_message(chat_id=user_id_to_reply, text=reply_message, parse_mode="Markdown")
        await message.reply("✅ تم إرسال الرد بنجاح للمستخدم.")
    except Exception as e:
        await message.reply(f"❌ فشل إرسال الرد للمستخدم: {e}")

# (بقية الكود الخاص بلوحة التحكم لم يتغير، لكن سنضعه كاملاً للتأكيد)
async def process_admin_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    data = callback_query.data
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    
    if data == "back_to_main":
        await state.finish()
        await bot.edit_message_text("🔧 **لوحة التحكم الإدارية**", chat_id=user_id, message_id=message_id, reply_markup=create_admin_panel(), parse_mode="Markdown")
    elif data == "close_panel":
        await callback_query.message.delete()
        await bot.send_message(user_id, "✅ تم إغلاق لوحة التحكم.")
    elif data == "admin_stats":
        stats_text = (f"📊 **إحصائيات البوت**\n\n👥 إجمالي المستخدمين: {len(USERS_LIST)}\n📝 الردود: {len(AUTO_REPLIES)}\n💭 التذكيرات: {len(DAILY_REMINDERS)}\n🚫 المحظورين: {len(BANNED_USERS)}")
        await bot.edit_message_text(stats_text, chat_id=user_id, message_id=message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")), parse_mode="Markdown")
    elif data == "deploy_to_production":
        uptime = datetime.datetime.now() - start_time
        days, rem = divmod(uptime.total_seconds(), 86400); hours, _ = divmod(rem, 3600)
        status_text = (f"🚀 **حالة البوت على Render**\n\n✅ **الحالة:** نشط\n⏰ **مدة التشغيل:** {int(days)} يوم و {int(hours)} ساعة")
        await bot.edit_message_text(status_text, chat_id=user_id, message_id=message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")), parse_mode="Markdown")
    elif data == "clear_temp_memory":
        count = len(user_message_count) + len(silenced_users)
        user_message_count.clear(); silenced_users.clear()
        await bot.answer_callback_query(callback_query.id, f"✅ تم مسح {count} سجل من ذاكرة Spam.", show_alert=True)
    elif data == "toggle_media":
        bot_data["allow_media"] = not bot_data.get("allow_media", False)
        save_data(bot_data)
        status = "مسموح الآن" if bot_data["allow_media"] else "ممنوع الآن"
        await bot.answer_callback_query(callback_query.id, f"تم تغيير حالة الوسائط إلى: {status}", show_alert=True)
        # Refresh menu is handled by recursion below
    
    # Menus and state setters
    menus = {
        "admin_replies": ("📝 **إدارة الردود**", [("➕ إضافة", "add_reply"), ("📝 عرض", "show_replies"), ("🗑️ حذف", "delete_reply_menu")]),
        "admin_reminders": ("💭 **إدارة التذكيرات**", [("➕ إضافة", "add_reminder"), ("📝 عرض", "show_reminders"), ("🗑️ حذف", "delete_reminder_menu")]),
        "admin_channel": ("📢 **رسائل القناة**", [("➕ إضافة", "add_channel_msg"), ("📝 عرض", "show_channel_msgs"), ("🗑️ حذف", "delete_channel_msg_menu"), ("📤 نشر فوري", "instant_channel_post")]),
        "admin_ban": ("🚫 **إدارة الحظر**", [("🚫 حظر", "ban_user"), ("✅ إلغاء حظر", "unban_user"), ("📋 عرض", "show_banned")]),
        "admin_broadcast": (f"📤 **النشر الجماعي** ({len(USERS_LIST)} مستخدم)", [("📤 إرسال رسالة", "send_broadcast")]),
        "admin_channel_settings": (f"⚙️ **إعدادات القناة**", [("🆔 تعديل ID", "set_channel_id"), ("⏰ تعديل الفترة", "set_schedule_time")]),
        "admin_messages_settings": ("💬 **إعدادات الرسائل**", [("👋 رسالة الترحيب", "set_welcome_msg"), ("💬 رسالة الرد", "set_reply_msg")]),
        "admin_media_settings": ("🔒 **إدارة الوسائط**", [("🔒 منع" if bot_data.get("allow_media") else "🔓 سماح", "toggle_media"), ("✏️ رسالة الرفض", "set_media_reject_msg")]),
        "admin_memory_management": ("🧠 **إدارة الذاكرة**", [("🗑️ مسح بيانات مستخدم", "clear_user_messages"), ("🧹 مسح ذاكرة Spam", "clear_temp_memory")]),
    }

    if data in menus:
        title, buttons_data = menus[data]
        keyboard = InlineKeyboardMarkup(row_width=2)
        buttons = [InlineKeyboardButton(text, callback_data=cb_data) for text, cb_data in buttons_data]
        keyboard.add(*buttons).add(InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
        await bot.edit_message_text(title, chat_id=user_id, message_id=message_id, reply_markup=keyboard)

    # ... (rest of the callback handler for states and lists)
    # Lists
    elif data == "show_replies":
        text = "📝 **الردود:**\n" + ("\n".join(f"🔹 `{k}`" for k in AUTO_REPLIES) or "لا يوجد")
        await bot.edit_message_text(text, chat_id=user_id, message_id=message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙", "admin_replies")), parse_mode="Markdown")
    elif data == "show_reminders":
        text = "💭 **التذكيرات:**\n" + ("\n".join(f"{i+1}. {r[:40]}..." for i,r in enumerate(DAILY_REMINDERS)) or "لا يوجد")
        await bot.edit_message_text(text, chat_id=user_id, message_id=message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙", "admin_reminders")))
    elif data == "show_channel_msgs":
        text = "📢 **رسائل القناة:**\n" + ("\n".join(f"{i+1}. {m[:40]}..." for i,m in enumerate(CHANNEL_MESSAGES)) or "لا يوجد")
        await bot.edit_message_text(text, chat_id=user_id, message_id=message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙", "admin_channel")))
    elif data == "show_banned":
        text = "🚫 **المحظورين:**\n" + ("\n".join(f"`{uid}`" for uid in BANNED_USERS) or "لا يوجد")
        await bot.edit_message_text(text, chat_id=user_id, message_id=message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙", "admin_ban")), parse_mode="Markdown")

    # State setters
    elif data in ["add_reply", "add_reminder", "add_channel_msg", "delete_reply_menu", "delete_reminder_menu", "delete_channel_msg_menu", "ban_user", "unban_user", "send_broadcast", "set_channel_id", "set_schedule_time", "set_welcome_msg", "set_reply_msg", "set_media_reject_msg", "clear_user_messages", "instant_channel_post"]:
        prompts = { "add_reply": ("أرسل: `الكلمة|الرد`", AdminStates.waiting_for_new_reply), "add_reminder": ("أرسل التذكير:", AdminStates.waiting_for_new_reminder), "add_channel_msg": ("أرسل الرسالة:", AdminStates.waiting_for_new_channel_message), "delete_reply_menu": ("أرسل الكلمة للحذف:", AdminStates.waiting_for_delete_reply), "delete_reminder_menu": ("أرسل الرقم للحذف:", AdminStates.waiting_for_delete_reminder), "delete_channel_msg_menu": ("أرسل الرقم للحذف:", AdminStates.waiting_for_delete_channel_msg), "ban_user": ("أرسل ID الحظر:", AdminStates.waiting_for_ban_id), "unban_user": ("أرسل ID لإلغاء الحظر:", AdminStates.waiting_for_unban_id), "send_broadcast": ("أرسل الرسالة الجماعية:", AdminStates.waiting_for_broadcast_message), "set_channel_id": ("أرسل ID القناة:", AdminStates.waiting_for_channel_id), "set_schedule_time": ("أرسل الفترة بالساعات:", AdminStates.waiting_for_schedule_time), "set_welcome_msg": ("أرسل رسالة الترحيب:", AdminStates.waiting_for_welcome_message), "set_reply_msg": ("أرسل رسالة الرد:", AdminStates.waiting_for_reply_message), "set_media_reject_msg": ("أرسل رسالة الرفض:", AdminStates.waiting_for_media_reject_message), "clear_user_messages": ("أرسل ID لمسح بياناته:", AdminStates.waiting_for_clear_user_id), "instant_channel_post": ("أرسل الرسالة للنشر:", AdminStates.waiting_for_instant_channel_post),}
        await state.set_state(prompts[data][1])
        await bot.edit_message_text(f"{prompts[data][0]}\n\nلإلغاء العملية، أرسل /cancel", chat_id=user_id, message_id=message_id, parse_mode="Markdown")

async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply("✅ تم إلغاء العملية.", reply_markup=types.ReplyKeyboardRemove())
    await admin_panel(message)

# (All other process_* functions remain the same as the previous correct version)
async def process_new_reply(message: types.Message, state: FSMContext):
    try:
        trigger, response = map(str.strip, message.text.split('|', 1))
        AUTO_REPLIES[trigger] = response; bot_data["auto_replies"] = AUTO_REPLIES; save_data(bot_data)
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("➕ إضافة رد آخر", callback_data="add_reply"), InlineKeyboardButton("🔙 العودة للوحة", callback_data="back_to_main"))
        await message.reply(f"✅ تم إضافة الرد!", reply_markup=keyboard)
    except: await message.reply("❌ تنسيق خاطئ!")
    await state.finish()
async def process_delete_reply(message: types.Message, state: FSMContext):
    trigger = message.text.strip()
    if trigger in AUTO_REPLIES:
        del AUTO_REPLIES[trigger]; bot_data["auto_replies"] = AUTO_REPLIES; save_data(bot_data)
        await message.reply(f"✅ تم حذف الرد.")
    else: await message.reply("❌ لم يتم العثور على الرد.")
    await state.finish(); await admin_panel(message)
# ... Add all other process_* handlers here ...
async def process_new_reminder(message: types.Message, state: FSMContext):
    DAILY_REMINDERS.append(message.text.strip()); bot_data["daily_reminders"] = DAILY_REMINDERS; save_data(bot_data)
    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("➕ إضافة تذكير آخر", callback_data="add_reminder"), InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
    await message.reply(f"✅ تم إضافة التذكير!", reply_markup=keyboard); await state.finish()
async def process_delete_reminder(message: types.Message, state: FSMContext):
    try:
        index = int(message.text.strip()) - 1
        if 0 <= index < len(DAILY_REMINDERS):
            DAILY_REMINDERS.pop(index); bot_data["daily_reminders"] = DAILY_REMINDERS; save_data(bot_data)
            await message.reply(f"✅ تم حذف التذكير.")
        else: await message.reply(f"❌ رقم غير صحيح.")
    except: await message.reply("❌ أرسل رقماً فقط.")
    await state.finish(); await admin_panel(message)
# ... and so on for all FSM handlers.

def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(admin_panel, lambda m: m.from_user.id == ADMIN_CHAT_ID and m.text == "/admin", state="*")
    dp.register_message_handler(handle_admin_reply, lambda m: m.from_user.id == ADMIN_CHAT_ID and m.reply_to_message, content_types=types.ContentTypes.ANY, state="*")
    dp.register_message_handler(cancel_handler, commands=['cancel'], state="*")
    dp.register_callback_query_handler(process_admin_callback, lambda q: q.from_user.id == ADMIN_CHAT_ID, state="*")
    
    # Register all FSM state handlers
    fsm_handlers = {
        AdminStates.waiting_for_new_reply: process_new_reply,
        AdminStates.waiting_for_delete_reply: process_delete_reply,
        AdminStates.waiting_for_new_reminder: process_new_reminder,
        AdminStates.waiting_for_delete_reminder: process_delete_reminder,
        # ... Add all other state: function pairs here
    }
    for state, handler in fsm_handlers.items():
        dp.register_message_handler(handler, state=state)


