import asyncio
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
from utils.helpers import *
from utils.tasks import send_channel_message

async def admin_panel(message: types.Message):
    await message.reply(
        "🔧 **لوحة التحكم الإدارية**\n\nأهلاً بك. اختر الإجراء المطلوب من القائمة:",
        reply_markup=create_admin_panel(), parse_mode="Markdown"
    )

async def handle_admin_reply(message: types.Message):
    if not message.reply_to_message or not message.reply_to_message.forward_from: return
    user_id_to_reply = message.reply_to_message.forward_from.id
    try:
        await message.forward(user_id_to_reply)
        await message.reply("✅ تم إرسال ردك للمستخدم بنجاح.")
    except Exception as e:
        await message.reply(f"❌ فشل إرسال الرد للمستخدم: {e}")

async def process_admin_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    data = callback_query.data
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    
    if data == "back_to_main":
        await state.finish()
        await bot.edit_message_text("🔧 **لوحة التحكم الإدارية**\n\nاختر الإجراء المطلوب:", chat_id=user_id, message_id=message_id, reply_markup=create_admin_panel(), parse_mode="Markdown")
    elif data == "close_panel": await callback_query.message.delete()
    elif data == "admin_stats":
        stats_text = (f"📊 **إحصائيات البوت**\n\n👥 **إجمالي المستخدمين:** {len(USERS_LIST)}\n📝 **الردود التلقائية:** {len(AUTO_REPLIES)}\n💭 **التذكيرات:** {len(DAILY_REMINDERS)}\n🚫 **المحظورين:** {len(BANNED_USERS)}")
        await bot.edit_message_text(stats_text, chat_id=user_id, message_id=message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")), parse_mode="Markdown")
    elif data == "deploy_to_production":
        uptime = datetime.datetime.now() - start_time; days, rem = divmod(uptime.total_seconds(), 86400); hours, _ = divmod(rem, 3600)
        status_text = (f"🚀 **حالة البوت على Render**\n\n✅ **الحالة:** نشط ويعمل\n⏰ **مدة التشغيل:** {int(days)} يوم و {int(hours)} ساعة")
        await bot.edit_message_text(status_text, chat_id=user_id, message_id=message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")), parse_mode="Markdown")
    elif data == "clear_temp_memory":
        count = len(user_message_count) + len(silenced_users); user_message_count.clear(); silenced_users.clear()
        await bot.answer_callback_query(callback_query.id, f"✅ تم مسح {count} سجل من ذاكرة Spam.", show_alert=True)
    elif data == "toggle_media":
        bot_data["allow_media"] = not bot_data.get("allow_media", False); save_data(bot_data)
        status = "✅ مسموح الآن" if bot_data["allow_media"] else "❌ ممنوع الآن"
        await bot.answer_callback_query(callback_query.id, f"تم تغيير حالة الوسائط إلى: {status}", show_alert=True)
        # Refresh menu is handled below in the menus section
    
    menus = {
        "admin_replies": "📝 **إدارة الردود التلقائية**", "admin_reminders": "💭 **إدارة التذكيرات اليومية**",
        "admin_channel": "📢 **إدارة رسائل القناة**", "admin_ban": "🚫 **إدارة الحظر**",
        "admin_broadcast": f"📤 **النشر الجماعي** (لـ {len(USERS_LIST)} مستخدم)", "admin_channel_settings": "⚙️ **إعدادات القناة**",
        "admin_messages_settings": "💬 **إعدادات الرسائل**", "admin_memory_management": "🧠 **إدارة الذاكرة**",
        "admin_media_settings": f"🔒 **إدارة الوسائط**\n\nالحالة الحالية: {'✅ مسموح' if bot_data.get('allow_media') else '❌ محظور'}"
    }
    buttons_map = {
        "admin_replies": [("➕ إضافة رد", "add_reply"), ("📝 عرض الردود", "show_replies"), ("🗑️ حذف رد", "delete_reply_menu")],
        "admin_reminders": [("➕ إضافة تذكير", "add_reminder"), ("📝 عرض التذكيرات", "show_reminders"), ("🗑️ حذف تذكير", "delete_reminder_menu")],
        "admin_channel": [("➕ إضافة رسالة", "add_channel_msg"), ("📝 عرض الرسائل", "show_channel_msgs"), ("🗑️ حذف رسالة", "delete_channel_msg_menu"), ("📤 نشر فوري", "instant_channel_post")],
        "admin_ban": [("🚫 حظر مستخدم", "ban_user"), ("✅ إلغاء حظر", "unban_user"), ("📋 قائمة المحظورين", "show_banned")],
        "admin_broadcast": [("📤 إرسال رسالة جماعية", "send_broadcast")],
        "admin_channel_settings": [("🆔 تعديل ID", "set_channel_id"), ("⏰ تعديل الفترة", "set_schedule_time")],
        "admin_messages_settings": [("👋 رسالة الترحيب", "set_welcome_msg"), ("💬 رسالة الرد", "set_reply_msg")],
        "admin_media_settings": [("🔒 منع الوسائط" if bot_data.get('allow_media') else "🔓 السماح بالوسائط", "toggle_media"), ("✏️ رسالة الرفض", "set_media_reject_msg")],
        "admin_memory_management": [("🗑️ مسح بيانات مستخدم", "clear_user_messages"), ("🧹 مسح ذاكرة Spam", "clear_temp_memory")]
    }
    if data in menus:
        keyboard = InlineKeyboardMarkup(row_width=2)
        buttons = [InlineKeyboardButton(text, cb) for text, cb in buttons_map[data]]
        keyboard.add(*buttons).add(InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="back_to_main"))
        await bot.edit_message_text(menus[data], chat_id=user_id, message_id=message_id, reply_markup=keyboard, parse_mode="Markdown")

    list_menus = {
        "show_replies": ("📝 **الردود الحالية:**", "admin_replies", [f"🔹 `{k}`" for k in AUTO_REPLIES.keys()]),
        "show_reminders": ("💭 **التذكيرات الحالية:**", "admin_reminders", [f"{i+1}. {r[:50]}..." for i, r in enumerate(DAILY_REMINDERS)]),
        "show_channel_msgs": ("📢 **رسائل القناة الحالية:**", "admin_channel", [f"{i+1}. {m[:50]}..." for i, m in enumerate(CHANNEL_MESSAGES)]),
        "show_banned": ("🚫 **قائمة المحظورين:**", "admin_ban", [f"`{uid}`" for uid in BANNED_USERS])
    }
    if data in list_menus:
        title, back_cb, items = list_menus[data]
        text = title + "\n\n" + ("\n".join(items) if items else "لا يوجد شيء لعرضه حالياً.")
        await bot.edit_message_text(text, chat_id=user_id, message_id=message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة", callback_data=back_cb)), parse_mode="Markdown")

    prompts = {
        "add_reply": ("📝 **إضافة رد**\n\nأرسل الرد بالتنسيق: `الكلمة|نص الرد`", AdminStates.waiting_for_new_reply),
        "add_reminder": ("💭 **إضافة تذكير**\n\nأرسل نص التذكير:", AdminStates.waiting_for_new_reminder),
        "delete_reply_menu": ("🗑️ **حذف رد**\n\nأرسل الكلمة المفتاحية للرد المراد حذفه:", AdminStates.waiting_for_delete_reply),
        "ban_user": ("🚫 **حظر مستخدم**\n\nأرسل ID المستخدم:", AdminStates.waiting_for_ban_id),
        "send_broadcast": ("📤 **رسالة جماعية**\n\nأرسل الرسالة لنشرها للجميع:", AdminStates.waiting_for_broadcast_message),
        # ... (Add other prompts here if needed)
    }
    if data in prompts:
        prompt_text, state_to_set = prompts[data]
        await state.set_state(state_to_set)
        await bot.edit_message_text(f"{prompt_text}\n\nلإلغاء العملية، أرسل /cancel", chat_id=user_id, message_id=message_id, parse_mode="Markdown")

async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply("✅ **تم إلغاء العملية بنجاح.**", reply_markup=types.ReplyKeyboardRemove())
    await admin_panel(message)

async def process_new_reply(message: types.Message, state: FSMContext):
    try:
        trigger, response = map(str.strip, message.text.split('|', 1))
        AUTO_REPLIES[trigger] = response; bot_data["auto_replies"] = AUTO_REPLIES; save_data(bot_data)
        reply_text = f"✅ **تم إضافة الرد بنجاح!**\n\n📝 **الكلمة:** `{trigger}`\n💬 **الرد:** {response}"
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("➕ إضافة رد آخر", callback_data="add_reply"), InlineKeyboardButton("🔙 العودة للوحة", callback_data="back_to_main"))
        await message.reply(reply_text, reply_markup=keyboard, parse_mode="Markdown")
        await state.finish()
    except ValueError:
        await message.reply("❌ **تنسيق خاطئ!**\nاستخدم: `الكلمة|الرد`\n\nأو أرسل /cancel للإلغاء.", parse_mode="Markdown")

# (بقية دوال process... مع رسائل محسنة)
async def process_delete_reply(message: types.Message, state: FSMContext):
    trigger = message.text.strip()
    if trigger in AUTO_REPLIES:
        del AUTO_REPLIES[trigger]; bot_data["auto_replies"] = AUTO_REPLIES; save_data(bot_data)
        await message.reply(f"🗑️ **تم حذف الرد بنجاح.**\n\nالكلمة المحذوفة: `{trigger}`", parse_mode="Markdown")
    else: await message.reply("❌ **خطأ:** لم يتم العثور على رد بهذه الكلمة.")
    await state.finish(); await admin_panel(message)
    
# (This is just a sample of the full file, assuming all other process functions are added similarly)
def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(admin_panel, lambda m: m.from_user.id == ADMIN_CHAT_ID and m.text == "/admin", state="*")
    dp.register_message_handler(handle_admin_reply, lambda m: m.from_user.id == ADMIN_CHAT_ID and m.reply_to_message, content_types=types.ContentTypes.ANY, state="*")
    dp.register_message_handler(cancel_handler, commands=['cancel'], state="*")
    dp.register_callback_query_handler(process_admin_callback, lambda q: q.from_user.id == ADMIN_CHAT_ID, state="*")
    
    dp.register_message_handler(process_new_reply, state=AdminStates.waiting_for_new_reply)
    dp.register_message_handler(process_delete_reply, state=AdminStates.waiting_for_delete_reply)
    # (Register all other FSM handlers here)


