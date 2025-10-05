from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
import data_store
from keyboards.inline.admin_keyboards import create_admin_panel, get_menu_keyboard, back_kb
import datetime

# This is the Golden Master version of the panel file.
# It contains the complete logic for handling all button presses and directing them to the correct state.

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
    """Central handler for all admin callback queries."""
    await cq.answer()
    if await state.get_state() is not None:
        await state.finish()
    
    d = cq.data
    
    # Main navigation
    if d == "close_panel": await cq.message.delete(); return
    if d == "back_to_main": await cq.message.edit_text("🔧 **لوحة التحكم الإدارية**", reply_markup=create_admin_panel()); return
    
    # Simple display actions
    if d == "admin_stats":
        stats_text = (f"📊 **إحصائيات البوت:**\n\n"
                      f"👥 المستخدمون: {len(data_store.bot_data.get('users', []))}\n"
                      f"🚫 المحظورون: {len(data_store.bot_data.get('banned_users', []))}\n"
                      f"💬 الردود المبرمجة: {len(data_store.bot_data.get('dynamic_replies', {}))}\n"
                      f"💡 التذكيرات: {len(data_store.bot_data.get('reminders', []))}")
        await cq.message.edit_text(stats_text, reply_markup=back_kb()); return
    
    if d == "deploy_status":
        uptime = datetime.datetime.now() - data_store.start_time
        status_text = f"🚀 **حالة النشر:**\n\n✅ نشط ومستقر\n⏰ مدة التشغيل: {str(uptime).split('.')[0]}"
        await cq.message.edit_text(status_text, reply_markup=back_kb()); return

    # Direct action for the "Test Channel" button
    if d == "test_channel":
        channel_id = data_store.bot_data.get('bot_settings', {}).get('channel_id')
        if channel_id:
            try:
                await bot.send_message(channel_id, "🧪 رسالة تجريبية من لوحة التحكم.")
                await cq.answer("✅ تم إرسال رسالة تجريبية بنجاح!", show_alert=True)
            except Exception as e:
                await cq.answer(f"❌ فشل الإرسال: {e}", show_alert=True)
        else:
            await cq.answer("⚠️ يرجى تحديد ID القناة أولاً!", show_alert=True)
        return

    # Displaying sub-menus
    menus = {
        "admin_dyn_replies": "📝 **الردود الديناميكية**", "admin_reminders": "💭 **إدارة التذكيرات**",
        "admin_channel": "📢 **منشورات القناة**", "admin_ban": "🚫 **إدارة الحظر**",
        "admin_broadcast": "📤 **النشر للجميع**", "admin_customize_ui": "🎨 **تخصيص الواجهة**",
        "admin_security": "🛡️ **الحماية والأمان**", "admin_memory_management": "🧠 **إدارة الذاكرة**",
        "admin_channel_settings": "⚙️ **إعدادات القناة**", "media_settings": "🖼️ **إدارة الوسائط**",
        "spam_settings": "🔧 **منع التكرار (Spam)**", "slow_mode_settings": "⏳ **التباطؤ (Slow Mode)**"
    }
    if d in menus:
        await cq.message.edit_text(f"{menus[d]}\n\nاختر الإجراء:", reply_markup=get_menu_keyboard(d)); return

    # Displaying lists of items
    lists = {
        "show_dyn_replies": ("📝 **الردود المبرمجة:**", "admin_dyn_replies", [f"▫️ `{k}`" for k in data_store.bot_data.get('dynamic_replies', {})]),
        "show_reminders": ("💭 **التذكيرات:**", "admin_reminders", [f"{i+1}. {r[:40]}..." for i, r in enumerate(data_store.bot_data.get('reminders', []))]),
        "show_channel_msgs": ("📢 **الرسائل التلقائية:**", "admin_channel", [f"{i+1}. {m[:40]}..." for i, m in enumerate(data_store.bot_data.get('channel_messages', []))]),
        "show_banned": ("🚫 **المحظورون:**", "admin_ban", [f"`{uid}`" for uid in data_store.bot_data.get('banned_users', [])])
    }
    if d in lists:
        title, back_cb, items = lists[d]
        text = title + "\n\n" + ("\n".join(items) if items else "لا يوجد شيء لعرضه.")
        await cq.message.edit_text(text, reply_markup=back_kb(back_cb)); return

    # Setting the state to wait for user input (This is the master list of all state-setting triggers)
    prompts = { 
        "add_dyn_reply": ("📝 أرسل **الكلمة المفتاحية**:", AdminStates.waiting_for_dyn_reply_keyword), 
        "delete_dyn_reply": ("🗑️ أرسل الكلمة المفتاحية للحذف:", AdminStates.waiting_for_dyn_reply_delete), 
        "add_reminder": ("💭 أرسل نص التذكير:", AdminStates.waiting_for_new_reminder), 
        "delete_reminder": ("🗑️ أرسل رقم التذكير للحذف:", AdminStates.waiting_for_delete_reminder), 
        "add_channel_msg": ("➕ أرسل نص الرسالة التلقائية:", AdminStates.waiting_for_new_channel_msg), 
        "delete_channel_msg": ("🗑️ أرسل رقم الرسالة للحذف:", AdminStates.waiting_for_delete_channel_msg), 
        "instant_channel_post": ("📤 أرسل المحتوى للنشر الفوري:", AdminStates.waiting_for_instant_channel_post), 
        "schedule_post": ("⏰ أرسل **المحتوى** (نص، صورة، ملصق) للجدولة:", AdminStates.waiting_for_scheduled_post_content), 
        "ban_user": ("🚫 أرسل ID المستخدم للحظر:", AdminStates.waiting_for_ban_id), 
        "unban_user": ("✅ أرسل ID المستخدم لإلغاء الحظر:", AdminStates.waiting_for_unban_id), 
        "send_broadcast": ("📤 أرسل رسالتك للجميع:", AdminStates.waiting_for_broadcast_message), 
        "edit_date_button": ("✏️ أرسل الاسم الجديد لزر التاريخ:", AdminStates.waiting_for_date_button_label), 
        "edit_time_button": ("✏️ أرسل الاسم الجديد لزر الساعة:", AdminStates.waiting_for_time_button_label), 
        "edit_reminder_button": ("✏️ أرسل الاسم الجديد لزر التذكير:", AdminStates.waiting_for_reminder_button_label), 
        "set_timezone": ("🌍 أرسل المنطقة الزمنية (مثال: Asia/Riyadh):", AdminStates.waiting_for_timezone), 
        "edit_welcome_msg": ("👋 أرسل نص الترحيب الجديد:", AdminStates.waiting_for_welcome_message), 
        "edit_reply_msg": ("💬 أرسل نص الرد التلقائي الجديد:", AdminStates.waiting_for_reply_message), 
        "set_channel_id": ("🆔 أرسل ID القناة الجديد (مع @ أو -):", AdminStates.waiting_for_channel_id), 
        "set_schedule_interval": ("⏰ أرسل فترة النشر بالساعات (مثال: 12):", AdminStates.waiting_for_schedule_interval), 
        "add_media_type": ("➕ أرسل نوع الوسائط (photo, video...):", AdminStates.waiting_for_add_media_type), 
        "remove_media_type": ("➖ أرسل نوع الوسائط للمنع:", AdminStates.waiting_for_remove_media_type), 
        "edit_media_reject_message": ("✍️ أرسل رسالة الرفض الجديدة:", AdminStates.waiting_for_media_reject_message),
        # --- THIS IS THE UPDATE ---
        "set_spam_limit": ("🔢 أرسل حد الرسائل (مثال: 5):", AdminStates.waiting_for_spam_limit),
        "set_spam_window": ("⏱️ أرسل الفترة بالثواني (مثال: 60):", AdminStates.waiting_for_spam_window),
        "set_slow_mode": ("⏳ أرسل فترة التباطؤ بالثواني (مثال: 5):", AdminStates.waiting_for_slow_mode),
        "clear_user_data": ("🗑️ أرسل ID المستخدم لمسح بياناته:", AdminStates.waiting_for_clear_user_id)
        # ---------------------------
    }
    if d in prompts:
        prompt_text, state_obj = prompts[d]
        await state.set_state(state_obj)
        await cq.message.edit_text(f"{prompt_text}\n\nلإلغاء العملية، أرسل /cancel."); return

def register_panel_handlers(dp: Dispatcher):
    """Registers the main admin command and callback handlers."""
    dp.register_message_handler(admin_panel_cmd, is_admin, commands=['admin'], state="*")
    dp.register_message_handler(admin_reply_cmd, is_admin, is_reply=True, content_types=types.ContentTypes.ANY, state="*")
    dp.register_callback_query_handler(callbacks_cmd, lambda c: c.from_user.id == ADMIN_CHAT_ID, state="*")
