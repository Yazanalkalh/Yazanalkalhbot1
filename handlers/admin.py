import asyncio
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# استيراد المكونات اللازمة من الملفات الأخرى
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
from utils.helpers import *
from utils.tasks import send_channel_message

# --- معالج لوحة التحكم الرئيسي ---

async def admin_panel(message: types.Message):
    """يعرض لوحة التحكم الرئيسية للمشرف."""
    await message.reply(
        "🔧 **لوحة التحكم الإدارية**\n\nاختر الخيار المناسب من القائمة أدناه:",
        reply_markup=create_admin_panel(),
        parse_mode="Markdown"
    )

async def handle_admin_reply(message: types.Message):
    """يعالج ردود المشرف على الرسائل المعاد توجيهها."""
    if not message.reply_to_message or not message.reply_to_message.forward_from:
        return

    admin_reply_text = message.text.strip()
    user_id = message.reply_to_message.forward_from.id

    try:
        reply_message = f"📩 **رد من الإدارة:**\n{admin_reply_text}"
        await bot.send_message(chat_id=user_id, text=reply_message, parse_mode="Markdown")
        await message.reply("✅ تم إرسال الرد بنجاح للمستخدم.")
    except Exception as e:
        await message.reply(f"❌ فشل إرسال الرد: {e}")

# --- المعالج الرئيسي لجميع أزرار لوحة التحكم ---

async def process_admin_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """يعالج جميع ضغطات الأزرار من لوحة التحكم."""
    await bot.answer_callback_query(callback_query.id)
    data = callback_query.data
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    
    # --- التنقل الأساسي ---
    if data == "back_to_main":
        await state.finish()
        await bot.edit_message_text("🔧 **لوحة التحكم الإدارية**\n\nاختر الخيار المناسب:", chat_id=user_id, message_id=message_id, reply_markup=create_admin_panel(), parse_mode="Markdown")
    elif data == "close_panel":
        await callback_query.message.delete()
        await bot.send_message(user_id, "✅ تم إغلاق لوحة التحكم.")

    # --- **إصلاح زر إحصائيات البوت** ---
    elif data == "admin_stats":
        stats_text = (
            f"📊 **إحصائيات البوت**\n\n"
            f"👥 إجمالي المستخدمين: {len(USERS_LIST)}\n"
            f"📝 الردود التلقائية: {len(AUTO_REPLIES)}\n"
            f"💭 التذكيرات اليومية: {len(DAILY_REMINDERS)}\n"
            f"📢 رسائل القناة: {len(CHANNEL_MESSAGES)}\n"
            f"🚫 المستخدمين المحظورين: {len(BANNED_USERS)}\n"
            f"💬 المحادثات النشطة: {len(user_threads)}\n"
            f"🔒 حالة الوسائط: {'مسموح' if bot_data.get('allow_media') else 'ممنوع'}"
        )
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="back_to_main"))
        await bot.edit_message_text(stats_text, chat_id=user_id, message_id=message_id, reply_markup=keyboard, parse_mode="Markdown")

    # --- القوائم الفرعية ---
    elif data == "admin_replies":
        keyboard = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton("➕ إضافة رد", callback_data="add_reply"), InlineKeyboardButton("📝 عرض الردود", callback_data="show_replies"), InlineKeyboardButton("🗑️ حذف رد", callback_data="delete_reply_menu"), InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
        await bot.edit_message_text("📝 **إدارة الردود التلقائية**", chat_id=user_id, message_id=message_id, reply_markup=keyboard)
    # ... (بقية القوائم تعمل بشكل صحيح)
    elif data == "admin_reminders":
        keyboard = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton("➕ إضافة تذكير", callback_data="add_reminder"), InlineKeyboardButton("📝 عرض التذكيرات", callback_data="show_reminders"), InlineKeyboardButton("🗑️ حذف تذكير", callback_data="delete_reminder_menu"), InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
        await bot.edit_message_text("💭 **إدارة التذكيرات اليومية**", chat_id=user_id, message_id=message_id, reply_markup=keyboard)
    elif data == "admin_channel":
        keyboard = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton("➕ إضافة رسالة", callback_data="add_channel_msg"), InlineKeyboardButton("📝 عرض الرسائل", callback_data="show_channel_msgs"), InlineKeyboardButton("🗑️ حذف رسالة", callback_data="delete_channel_msg_menu"), InlineKeyboardButton("📤 نشر فوري", callback_data="instant_channel_post"), InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
        await bot.edit_message_text("📢 **إدارة رسائل القناة**", chat_id=user_id, message_id=message_id, reply_markup=keyboard)
    elif data == "admin_ban":
        keyboard = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton("🚫 حظر مستخدم", callback_data="ban_user"), InlineKeyboardButton("✅ إلغاء حظر", callback_data="unban_user"), InlineKeyboardButton("📋 قائمة المحظورين", callback_data="show_banned"), InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
        await bot.edit_message_text("🚫 **إدارة الحظر**", chat_id=user_id, message_id=message_id, reply_markup=keyboard)
    elif data == "admin_broadcast":
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("📤 إرسال رسالة جماعية", callback_data="send_broadcast"), InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
        await bot.edit_message_text(f"📤 **النشر الجماعي**\n\nعدد المستخدمين: {len(USERS_LIST)}", chat_id=user_id, message_id=message_id, reply_markup=keyboard)
    elif data == "admin_channel_settings":
        current_channel = bot_data.get("channel_id", "غير محدد")
        interval = bot_data.get("schedule_interval_seconds", 86400)
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("🆔 تعديل معرف القناة", callback_data="set_channel_id"), InlineKeyboardButton("⏰ تعديل فترة النشر", callback_data="set_schedule_time"), InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
        await bot.edit_message_text(f"⚙️ **إعدادات القناة**\n\n📢 القناة الحالية: `{current_channel}`\n⏰ فترة النشر: {interval // 3600} ساعة", chat_id=user_id, message_id=message_id, reply_markup=keyboard, parse_mode="Markdown")
    elif data == "admin_messages_settings":
        welcome_msg = "✅ محدد" if bot_data.get("welcome_message") else "❌ غير محدد"
        reply_msg = "✅ محدد" if bot_data.get("reply_message") else "❌ غير محدد"
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("👋 رسالة الترحيب", callback_data="set_welcome_msg"), InlineKeyboardButton("💬 رسالة الرد التلقائي", callback_data="set_reply_msg"), InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
        await bot.edit_message_text(f"💬 **إعدادات الرسائل**\n\n👋 رسالة الترحيب: {welcome_msg}\n💬 الرد التلقائي: {reply_msg}", chat_id=user_id, message_id=message_id, reply_markup=keyboard)
    elif data == "admin_media_settings":
        media_status_text = "✅ مسموح" if bot_data.get("allow_media", False) else "❌ محظور"
        button_text = "🔒 منع الوسائط" if bot_data.get("allow_media", False) else "🔓 السماح بالوسائط"
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(button_text, callback_data="toggle_media"), InlineKeyboardButton("✏️ رسالة الرفض", callback_data="set_media_reject_msg"), InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
        await bot.edit_message_text(f"🔒 **إدارة الوسائط**\n\nالحالة الحالية: {media_status_text}\nالوسائط المرفوضة: {bot_data.get('rejected_media_count', 0)}", chat_id=user_id, message_id=message_id, reply_markup=keyboard)
    elif data == "admin_memory_management":
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("🗑️ مسح بيانات مستخدم", callback_data="clear_user_messages"), InlineKeyboardButton("🧹 مسح ذاكرة Spam", callback_data="clear_temp_memory"), InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
        await bot.edit_message_text(f"🧠 **إدارة الذاكرة**\n\nالرسائل المحفوظة: {len(user_messages)}\nالمحادثات النشطة: {len(user_threads)}", chat_id=user_id, message_id=message_id, reply_markup=keyboard)

    # --- إصلاح زر الوسائط وحالة الإنتاج ---
    elif data == "toggle_media":
        current_status = bot_data.get("allow_media", False)
        bot_data["allow_media"] = not current_status
        save_data(bot_data)
        new_status_text = "✅ مسموح الآن" if not current_status else "❌ ممنوع الآن"
        await bot.answer_callback_query(callback_query.id, f"تم تغيير حالة استقبال الوسائط إلى: {new_status_text}", show_alert=True)
        # Refresh the menu
        media_status_text = "✅ مسموح" if bot_data["allow_media"] else "❌ محظور"
        button_text = "🔒 منع الوسائط" if bot_data["allow_media"] else "🔓 السماح بالوسائط"
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(button_text, callback_data="toggle_media"), InlineKeyboardButton("✏️ رسالة الرفض", callback_data="set_media_reject_msg"), InlineKeyboardButton("🔙 العودة", callback_data="back_to_main"))
        await bot.edit_message_text(f"🔒 **إدارة الوسائط**\n\nالحالة الحالية: {media_status_text}", chat_id=user_id, message_id=message_id, reply_markup=keyboard)

    elif data == "deploy_to_production":
        uptime = datetime.datetime.now() - start_time
        days, rem = divmod(uptime.total_seconds(), 86400); hours, rem = divmod(rem, 3600); minutes, _ = divmod(rem, 60)
        status_text = (f"🚀 **حالة البوت على خادم Render**\n\n✅ **الحالة:** نشط ويعمل\n⏰ **مدة التشغيل:** {int(days)} يوم و {int(hours)} ساعة\n📊 **إجمالي المستخدمين:** {len(USERS_LIST)}")
        await bot.edit_message_text(status_text, chat_id=user_id, message_id=message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")), parse_mode="Markdown")

    # --- عرض القوائم ---
    elif data == "show_replies":
        text = "📝 **الردود التلقائية:**\n\n" + ("\n".join([f"🔹 `{k}`" for k in AUTO_REPLIES.keys()]) or "لا توجد ردود.")
        await bot.edit_message_text(text, chat_id=user_id, message_id=message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة", callback_data="admin_replies")), parse_mode="Markdown")
    # ... (بقية قوائم العرض تعمل)
    elif data == "show_reminders":
        text = "💭 **التذكيرات اليومية:**\n\n" + ("\n".join([f"{i+1}. {r[:50]}..." for i, r in enumerate(DAILY_REMINDERS)]) or "لا توجد تذكيرات.")
        await bot.edit_message_text(text, chat_id=user_id, message_id=message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة", callback_data="admin_reminders")))
    elif data == "show_channel_msgs":
        text = "📢 **رسائل القناة:**\n\n" + ("\n".join([f"{i+1}. {m[:50]}..." for i, m in enumerate(CHANNEL_MESSAGES)]) or "لا توجد رسائل.")
        await bot.edit_message_text(text, chat_id=user_id, message_id=message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة", callback_data="admin_channel")))
    elif data == "show_banned":
        text = "🚫 **قائمة المحظورين:**\n\n" + ("\n".join([f"`{uid}`" for uid in BANNED_USERS]) or "لا يوجد محظورين.")
        await bot.edit_message_text(text, chat_id=user_id, message_id=message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة", callback_data="admin_ban")), parse_mode="Markdown")


    # --- الإجراءات (تفعيل الحالات) ---
    elif data in ["add_reply", "add_reminder", "add_channel_msg", "delete_reply_menu", "delete_reminder_menu", "delete_channel_msg_menu", "ban_user", "unban_user", "send_broadcast", "set_channel_id", "set_schedule_time", "set_welcome_msg", "set_reply_msg", "set_media_reject_msg", "clear_user_messages", "instant_channel_post"]:
        prompts = { "add_reply": ("📝 أرسل الرد: `الكلمة|الرد`", AdminStates.waiting_for_new_reply), "add_reminder": ("💭 أرسل نص التذكير:", AdminStates.waiting_for_new_reminder), "add_channel_msg": ("📢 أرسل نص الرسالة:", AdminStates.waiting_for_new_channel_message), "delete_reply_menu": ("🗑️ أرسل الكلمة المفتاحية للحذف:", AdminStates.waiting_for_delete_reply), "delete_reminder_menu": ("🗑️ أرسل رقم التذكير للحذف:", AdminStates.waiting_for_delete_reminder), "delete_channel_msg_menu": ("🗑️ أرسل رقم الرسالة للحذف:", AdminStates.waiting_for_delete_channel_msg), "ban_user": ("🚫 أرسل ID المستخدم للحظر:", AdminStates.waiting_for_ban_id), "unban_user": ("✅ أرسل ID المستخدم لإلغاء الحظر:", AdminStates.waiting_for_unban_id), "send_broadcast": ("📤 أرسل الرسالة الجماعية:", AdminStates.waiting_for_broadcast_message), "set_channel_id": ("🆔 أرسل معرف القناة الجديد:", AdminStates.waiting_for_channel_id), "set_schedule_time": ("⏰ أرسل الفترة بالساعات:", AdminStates.waiting_for_schedule_time), "set_welcome_msg": ("👋 أرسل رسالة الترحيب الجديدة:", AdminStates.waiting_for_welcome_message), "set_reply_msg": ("💬 أرسل رسالة الرد الجديدة:", AdminStates.waiting_for_reply_message), "set_media_reject_msg": ("✏️ أرسل رسالة الرفض الجديدة:", AdminStates.waiting_for_media_reject_message), "clear_user_messages": ("🗑️ أرسل ID المستخدم لمسح بياناته:", AdminStates.waiting_for_clear_user_id), "instant_channel_post": ("📤 أرسل الرسالة للنشر الفوري:", AdminStates.waiting_for_instant_channel_post),}
        prompt_text, state_to_set = prompts[data]
        await state_to_set.set()
        await bot.edit_message_text(f"{prompt_text}\n\nلإلغاء العملية، أرسل /cancel", chat_id=user_id, message_id=message_id, parse_mode="Markdown")

    # --- **إصلاح زر مسح الذاكرة المؤقتة** ---
    elif data == "clear_temp_memory":
        count_before = len(user_message_count) + len(silenced_users)
        user_message_count.clear()
        silenced_users.clear()
        count_after = len(user_message_count) + len(silenced_users)
        await bot.answer_callback_query(callback_query.id, f"✅ تم مسح {count_before} سجل من ذاكرة Spam.", show_alert=True)

# (بقية الدوال هنا كما هي بدون تغيير)
# ...
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply("✅ تم إلغاء العملية.", reply_markup=types.ReplyKeyboardRemove())
    await admin_panel(message)
async def process_new_reply(message: types.Message, state: FSMContext):
    try:
        trigger, response = map(str.strip, message.text.split('|', 1))
        AUTO_REPLIES[trigger] = response; bot_data["auto_replies"] = AUTO_REPLIES; save_data(bot_data)
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("➕ إضافة رد آخر", callback_data="add_reply"), InlineKeyboardButton("🔙 العودة للوحة", callback_data="back_to_main"))
        await message.reply(f"✅ تم إضافة الرد بنجاح!", reply_markup=keyboard)
    except: await message.reply("❌ تنسيق خاطئ! استخدم: `الكلمة|الرد`")
    await state.finish()
async def process_new_reminder(message: types.Message, state: FSMContext):
    DAILY_REMINDERS.append(message.text.strip()); bot_data["daily_reminders"] = DAILY_REMINDERS; save_data(bot_data)
    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("➕ إضافة تذكير آخر", callback_data="add_reminder"), InlineKeyboardButton("🔙 العودة للوحة", callback_data="back_to_main"))
    await message.reply(f"✅ تم إضافة التذكير بنجاح!", reply_markup=keyboard)
    await state.finish()
async def process_new_channel_message(message: types.Message, state: FSMContext):
    CHANNEL_MESSAGES.append(message.text.strip()); bot_data["channel_messages"] = CHANNEL_MESSAGES; save_data(bot_data)
    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("➕ إضافة رسالة أخرى", callback_data="add_channel_msg"), InlineKeyboardButton("🔙 العودة للوحة", callback_data="back_to_main"))
    await message.reply(f"✅ تم إضافة الرسالة بنجاح!", reply_markup=keyboard)
    await state.finish()
async def process_delete_reply(message: types.Message, state: FSMContext):
    trigger = message.text.strip()
    if trigger in AUTO_REPLIES:
        del AUTO_REPLIES[trigger]; bot_data["auto_replies"] = AUTO_REPLIES; save_data(bot_data)
        await message.reply(f"✅ تم حذف الرد `{trigger}` بنجاح.")
    else: await message.reply("❌ لم يتم العثور على الرد.")
    await state.finish()
    await admin_panel(message)
async def process_delete_reminder(message: types.Message, state: FSMContext):
    try:
        index = int(message.text.strip()) - 1
        if 0 <= index < len(DAILY_REMINDERS):
            DAILY_REMINDERS.pop(index); bot_data["daily_reminders"] = DAILY_REMINDERS; save_data(bot_data)
            await message.reply(f"✅ تم حذف التذكير رقم {index+1} بنجاح.")
        else: await message.reply(f"❌ رقم غير صحيح.")
    except: await message.reply("❌ إدخال خاطئ. أرسل رقماً فقط.")
    await state.finish()
    await admin_panel(message)
async def process_delete_channel_msg(message: types.Message, state: FSMContext):
    try:
        index = int(message.text.strip()) - 1
        if 0 <= index < len(CHANNEL_MESSAGES):
            CHANNEL_MESSAGES.pop(index); bot_data["channel_messages"] = CHANNEL_MESSAGES; save_data(bot_data)
            await message.reply(f"✅ تم حذف الرسالة رقم {index+1} بنجاح.")
        else: await message.reply(f"❌ رقم غير صحيح.")
    except: await message.reply("❌ إدخال خاطئ. أرسل رقماً فقط.")
    await state.finish()
    await admin_panel(message)
async def process_ban_user(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
        BANNED_USERS.add(user_id); bot_data["banned_users"] = list(BANNED_USERS); save_data(bot_data)
        await message.reply(f"✅ تم حظر المستخدم `{user_id}`.")
    except: await message.reply("❌ إدخال خاطئ. أرسل ID رقمي.")
    await state.finish()
    await admin_panel(message)
async def process_unban_user(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
        BANNED_USERS.discard(user_id); bot_data["banned_users"] = list(BANNED_USERS); save_data(bot_data)
        await message.reply(f"✅ تم إلغاء حظر المستخدم `{user_id}`.")
    except: await message.reply("❌ إدخال خاطئ. أرسل ID رقمي.")
    await state.finish()
    await admin_panel(message)
async def process_broadcast(message: types.Message, state: FSMContext):
    success, failed = 0, 0
    await message.reply(f"📤 بدء الإرسال لـ {len(USERS_LIST)} مستخدم...")
    for user_id in USERS_LIST:
        try:
            await bot.send_message(user_id, message.text); success += 1
        except: failed += 1
        await asyncio.sleep(0.1)
    await message.reply(f"✅ تمت عملية الإرسال.\n\nالنتائج:\n- نجح: {success}\n- فشل: {failed}")
    await state.finish()
async def process_channel_id(message: types.Message, state: FSMContext):
    bot_data["channel_id"] = message.text.strip(); save_data(bot_data)
    await message.reply(f"✅ تم تحديث معرف القناة إلى: `{bot_data['channel_id']}`")
    await state.finish()
    await admin_panel(message)
async def process_schedule_time(message: types.Message, state: FSMContext):
    try:
        hours = float(message.text.strip())
        bot_data["schedule_interval_seconds"] = int(hours * 3600); save_data(bot_data)
        await message.reply(f"✅ تم تحديث فترة النشر إلى كل {hours} ساعة.")
    except: await message.reply("❌ إدخال خاطئ. أرسل رقماً فقط.")
    await state.finish()
    await admin_panel(message)
async def process_welcome_message(message: types.Message, state: FSMContext):
    bot_data["welcome_message"] = message.text.strip(); save_data(bot_data)
    await message.reply(f"✅ تم تحديث رسالة الترحيب.")
    await state.finish()
    await admin_panel(message)
async def process_reply_message(message: types.Message, state: FSMContext):
    bot_data["reply_message"] = message.text.strip(); save_data(bot_data)
    await message.reply(f"✅ تم تحديث رسالة الرد التلقائي.")
    await state.finish()
    await admin_panel(message)
async def process_media_reject_message(message: types.Message, state: FSMContext):
    bot_data["media_reject_message"] = message.text.strip(); save_data(bot_data)
    await message.reply(f"✅ تم تحديث رسالة رفض الوسائط.")
    await state.finish()
    await admin_panel(message)
async def process_clear_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
        if user_id in user_threads: del user_threads[user_id]
        if user_id in user_message_count: del user_message_count[user_id]
        await message.reply(f"✅ تم مسح البيانات المؤقتة للمستخدم `{user_id}`.")
    except: await message.reply("❌ إدخال خاطئ. أرسل ID رقمي.")
    await state.finish()
    await admin_panel(message)
async def process_instant_channel_post(message: types.Message, state: FSMContext):
    if await send_channel_message(custom_message=message.text):
        await message.reply("✅ تم النشر في القناة بنجاح!")
    else:
        await message.reply("❌ فشل النشر! تأكد من إعدادات القناة.")
    await state.finish()

def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(admin_panel, lambda m: m.from_user.id == ADMIN_CHAT_ID and m.text == "/admin", state="*")
    dp.register_message_handler(handle_admin_reply, lambda m: m.from_user.id == ADMIN_CHAT_ID and m.reply_to_message, content_types=types.ContentTypes.TEXT, state="*")
    dp.register_message_handler(cancel_handler, commands=['cancel'], state="*")
    dp.register_callback_query_handler(process_admin_callback, lambda q: q.from_user.id == ADMIN_CHAT_ID, state="*")
    # Register FSM handlers
    dp.register_message_handler(process_new_reply, state=AdminStates.waiting_for_new_reply)
    dp.register_message_handler(process_new_reminder, state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(process_new_channel_message, state=AdminStates.waiting_for_new_channel_message)
    dp.register_message_handler(process_delete_reply, state=AdminStates.waiting_for_delete_reply)
    dp.register_message_handler(process_delete_reminder, state=AdminStates.waiting_for_delete_reminder)
    dp.register_message_handler(process_delete_channel_msg, state=AdminStates.waiting_for_delete_channel_msg)
    dp.register_message_handler(process_ban_user, state=AdminStates.waiting_for_ban_id)
    dp.register_message_handler(process_unban_user, state=AdminStates.waiting_for_unban_id)
    dp.register_message_handler(process_broadcast, state=AdminStates.waiting_for_broadcast_message)
    dp.register_message_handler(process_channel_id, state=AdminStates.waiting_for_channel_id)
    dp.register_message_handler(process_schedule_time, state=AdminStates.waiting_for_schedule_time)
    dp.register_message_handler(process_welcome_message, state=AdminStates.waiting_for_welcome_message)
    dp.register_message_handler(process_reply_message, state=AdminStates.waiting_for_reply_message)
    dp.register_message_handler(process_media_reject_message, state=AdminStates.waiting_for_media_reject_message)
    dp.register_message_handler(process_clear_user_id, state=AdminStates.waiting_for_clear_user_id)
    dp.register_message_handler(process_instant_channel_post, state=AdminStates.waiting_for_instant_channel_post)


