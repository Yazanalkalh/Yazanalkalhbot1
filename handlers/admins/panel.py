from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
import data_store
from keyboards.inline.admin_keyboards import create_admin_panel, get_menu_keyboard, back_kb
import datetime

# This is the final, definitive, and fixed version of the main admin panel.
# The handlers have been corrected to not interfere with other admin panels or FSM states.

def is_admin(message: types.Message):
    """A filter to check if the user is an admin."""
    return message.from_user.id == ADMIN_CHAT_ID

async def admin_panel_cmd(m: types.Message, state: FSMContext):
    """Handler for the /admin command."""
    if await state.get_state() is not None:
        await state.finish()
    await m.reply("🔧 **لوحة التحكم الإدارية**", reply_markup=create_admin_panel())

async def admin_reply_cmd(m: types.Message, state: FSMContext):
    """Handler for admin replies to forwarded messages."""
    if not m.reply_to_message: return
    link = data_store.forwarded_message_links.get(m.reply_to_message.message_id)
    if link:
        try:
            await m.copy_to(link["user_id"], reply_to_message_id=link["original_message_id"])
            await m.reply("✅ **تم إرسال الرد بنجاح.**")
        except Exception as e:
            await m.reply(f"❌ **فشل إرسال الرد:** {e}")

async def callbacks_cmd(cq: types.CallbackQuery, state: FSMContext):
    """Central handler for the main /admin panel callback queries."""
    await cq.answer()
    if await state.get_state() is not None:
        await state.finish()
    
    d = cq.data
    
    # Main navigation
    if d == "close_panel": await cq.message.delete(); return
    if d == "back_to_main": await cq.message.edit_text("🔧 **لوحة التحكم الإدارية**", reply_markup=create_admin_panel()); return
    
    # Interactive List Deletion
    if d.startswith("del_reminder_"):
        idx = int(d.split('_')[-1])
        reminders = data_store.bot_data.get('reminders', [])
        if 0 <= idx < len(reminders):
            reminders.pop(idx)
            data_store.save_data()
            await cq.answer("✅ تم الحذف بنجاح.")
            # Refresh the list view
            cq.data = "show_reminders"
            await callbacks_cmd(cq, state)
        return

    if d.startswith("del_dyn_reply_"):
        keyword = d.replace("del_dyn_reply_", "")
        if keyword in data_store.bot_data.get('dynamic_replies', {}):
            del data_store.bot_data['dynamic_replies'][keyword]
            data_store.save_data()
            await cq.answer("✅ تم الحذف بنجاح.")
            # Refresh the list view
            cq.data = "show_dyn_replies"
            await callbacks_cmd(cq, state)
        return
        
    # Other handlers
    if d == "admin_stats":
        stats_text = (f"📊 **إحصائيات البوت:**\n\n"
                      f"👥 المستخدمون: {len(data_store.bot_data.get('users', []))}\n"
                      f"🚫 المحظورون: {len(data_store.bot_data.get('banned_users', []))}\n"
                      f"💬 الردود: {len(data_store.bot_data.get('dynamic_replies', {}))}\n"
                      f"💡 التذكيرات: {len(data_store.bot_data.get('reminders', []))}")
        await cq.message.edit_text(stats_text, reply_markup=back_kb()); return
    
    if d == "deploy_status":
        uptime = datetime.datetime.now() - data_store.start_time
        status_text = f"🚀 **حالة النشر:**\n\n✅ نشط\n⏰ مدة التشغيل: {str(uptime).split('.')[0]}"
        await cq.message.edit_text(status_text, reply_markup=back_kb()); return

    if d == "test_channel":
        channel_id = data_store.bot_data.get('bot_settings', {}).get('channel_id')
        if channel_id:
            try:
                await bot.send_message(channel_id, "🧪 رسالة تجريبية.")
                await cq.answer("✅ تم إرسال الرسالة!", show_alert=True)
            except Exception as e: await cq.answer(f"❌ فشل: {e}", show_alert=True)
        else: await cq.answer("⚠️ حدد ID القناة أولاً!", show_alert=True)
        return

    menus = {"admin_dyn_replies": "📝 **الردود الديناميكية**", "admin_reminders": "💭 **إدارة التذكيرات**", "admin_channel": "📢 **منشورات القناة**", "admin_ban": "🚫 **إدارة الحظر**", "admin_broadcast": "📤 **النشر للجميع**", "admin_customize_ui": "🎨 **تخصيص الواجهة**", "admin_security": "🛡️ **الحماية والأمان**", "admin_memory_management": "🧠 **إدارة الذاكرة**", "admin_channel_settings": "⚙️ **إعدادات القناة**", "media_settings": "🖼️ **إدارة الوسائط**", "spam_settings": "🔧 **منع التكرار**", "slow_mode_settings": "⏳ **التباطؤ**"}
    if d in menus:
        await cq.message.edit_text(f"{menus[d]}\n\nاختر الإجراء:", reply_markup=get_menu_keyboard(d)); return

    if d == "show_reminders":
        reminders = data_store.bot_data.get('reminders', [])
        await state.update_data(reminders_view=list(reminders)) # Store a copy for safe deletion
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        text = "💭 **قائمة التذكيرات:**\n\nاضغط لحذف تذكير."
        if not reminders: text = "💭 **القائمة فارغة.**"
        else:
            for i, reminder in enumerate(reminders):
                keyboard.add(types.InlineKeyboardButton(f"🗑️ {reminder[:50]}...", callback_data=f"del_reminder_{i}"))
        keyboard.add(types.InlineKeyboardButton("🔙 العودة", callback_data="admin_reminders"))
        await cq.message.edit_text(text, reply_markup=keyboard)
        return

    if d == "show_dyn_replies":
        replies = data_store.bot_data.get('dynamic_replies', {})
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        text = "📝 **قائمة الردود:**\n\nاضغط لحذف رد."
        if not replies: text = "📝 **القائمة فارغة.**"
        else:
            for keyword in sorted(replies.keys()):
                keyboard.add(types.InlineKeyboardButton(f"🗑️ `{keyword}`", callback_data=f"del_dyn_reply_{keyword}"))
        keyboard.add(types.InlineKeyboardButton("🔙 العودة", callback_data="admin_dyn_replies"))
        await cq.message.edit_text(text, reply_markup=keyboard)
        return
    
    lists = {
        "show_channel_msgs": ("📢 **الرسائل التلقائية:**", "admin_channel", [f"{i+1}. {m[:40]}..." for i, m in enumerate(data_store.bot_data.get('channel_messages', []))]),
        "show_banned": ("🚫 **المحظورون:**", "admin_ban", [f"`{uid}`" for uid in data_store.bot_data.get('banned_users', [])])
    }
    if d in lists:
        title, back_cb, items = lists[d]
        text = title + "\n\n" + ("\n".join(items) if items else "لا يوجد شيء لعرضه.")
        await cq.message.edit_text(text, reply_markup=back_kb(back_cb)); return

    prompts = { 
        "add_dyn_reply": ("📝 أرسل **الكلمة المفتاحية**:", AdminStates.waiting_for_dyn_reply_keyword), 
        "delete_dyn_reply": ("🗑️ أرسل الكلمة المفتاحية للحذف:", AdminStates.waiting_for_dyn_reply_delete),
        "import_dyn_replies": ("📥 أرسل ملف الردود (.txt):", AdminStates.waiting_for_dyn_replies_file),
        "add_reminder": ("💭 أرسل نص التذكير:", AdminStates.waiting_for_new_reminder), 
        "delete_reminder": ("🗑️ أرسل رقم التذكير للحذف:", AdminStates.waiting_for_delete_reminder),
        "import_reminders": ("📥 أرسل ملف التذكيرات (.txt):", AdminStates.waiting_for_reminders_file),
        "add_channel_msg": ("➕ أرسل نص رسالة القناة:", AdminStates.waiting_for_new_channel_msg), 
        "delete_channel_msg": ("🗑️ أرسل رقم الرسالة للحذف:", AdminStates.waiting_for_delete_channel_msg), 
        "instant_channel_post": ("📤 أرسل المحتوى للنشر الفوري:", AdminStates.waiting_for_instant_channel_post), 
        "schedule_post": ("⏰ أرسل **المحتوى** للجدولة:", AdminStates.waiting_for_scheduled_post_content), 
        "ban_user": ("🚫 أرسل ID المستخدم للحظر:", AdminStates.waiting_for_ban_id), 
        "unban_user": ("✅ أرسل ID المستخدم لإلغاء الحظر:", AdminStates.waiting_for_unban_id), 
        "send_broadcast": ("📤 أرسل رسالتك للجميع:", AdminStates.waiting_for_broadcast_message), 
        "edit_date_button": ("✏️ أرسل اسم زر التاريخ:", AdminStates.waiting_for_date_button_label), 
        "edit_time_button": ("✏️ أرسل اسم زر الساعة:", AdminStates.waiting_for_time_button_label), 
        "edit_reminder_button": ("✏️ أرسل اسم زر التذكير:", AdminStates.waiting_for_reminder_button_label), 
        "set_timezone": ("🌍 أرسل المنطقة الزمنية:", AdminStates.waiting_for_timezone), 
        "edit_welcome_msg": ("👋 أرسل نص الترحيب:", AdminStates.waiting_for_welcome_message), 
        "edit_reply_msg": ("💬 أرسل نص الرد:", AdminStates.waiting_for_reply_message), 
        "set_channel_id": ("🆔 أرسل ID القناة:", AdminStates.waiting_for_channel_id), 
        "set_schedule_interval": ("⏰ أرسل فترة النشر بالساعات:", AdminStates.waiting_for_schedule_interval), 
        "add_media_type": ("➕ أرسل نوع الوسائط:", AdminStates.waiting_for_add_media_type), 
        "remove_media_type": ("➖ أرسل نوع الوسائط للمنع:", AdminStates.waiting_for_remove_media_type), 
        "edit_media_reject_message": ("✍️ أرسل رسالة الرفض:", AdminStates.waiting_for_media_reject_message),
        "set_spam_limit": ("🔢 أرسل حد الرسائل:", AdminStates.waiting_for_spam_limit),
        "set_spam_window": ("⏱️ أرسل الفترة بالثواني:", AdminStates.waiting_for_spam_window),
        "set_slow_mode": ("⏳ أرسل فترة التباطؤ بالثواني:", AdminStates.waiting_for_slow_mode),
        "clear_user_data": ("🗑️ أرسل ID المستخدم لمسح بياناته:", AdminStates.waiting_for_clear_user_id)
    }
    if d in prompts:
        prompt_text, state_obj = prompts[d]
        await state.set_state(state_obj)
        await cq.message.edit_text(f"{prompt_text}\n\nلإلغاء العملية، أرسل /cancel."); return

def register_panel_handlers(dp: Dispatcher):
    """Registers the main admin command and callback handlers."""
    dp.register_message_handler(admin_panel_cmd, is_admin, commands=['admin'], state="*")
    
    # --- CRITICAL FIX 1: This handler will now ONLY trigger if the admin is NOT in any state ---
    dp.register_message_handler(admin_reply_cmd, is_admin, is_reply=True, content_types=types.ContentTypes.ANY, state=None)
    
    # --- CRITICAL FIX 2: This handler is now more specific and won't steal callbacks from other panels ---
    dp.register_callback_query_handler(
        callbacks_cmd, 
        is_admin, 
        # This lambda ensures this handler only catches callbacks that DO NOT belong to the advanced panels.
        lambda c: not c.data.startswith("adv_") and not c.data.startswith("tm_"),
        state="*"
    )
