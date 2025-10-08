import datetime
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
# ✅ تم الإصلاح: لم نعد نستخدم data_store هنا
from utils import database, texts
from keyboards.inline.admin_keyboards import create_admin_panel, get_menu_keyboard, back_kb

def is_admin(message: types.Message):
    """A filter to check if the user is an admin."""
    return message.from_user.id == ADMIN_CHAT_ID

async def admin_panel_cmd(m: types.Message, state: FSMContext):
    """Handler for the /admin command."""
    if await state.get_state() is not None:
        await state.finish()
    await m.reply(texts.get_text("admin_panel_title"), reply_markup=create_admin_panel())

async def admin_reply_cmd(m: types.Message, state: FSMContext):
    """Handler for admin replies to forwarded messages. Now uses the database."""
    if not m.reply_to_message: return
    
    # ✅ تم الإصلاح: جلب رابط الرسالة من قاعدة البيانات لضمان عدم فقدانه
    link = database.get_forward_link(m.reply_to_message.message_id)
    
    if link:
        try:
            await m.copy_to(link["user_id"], reply_to_message_id=link["original_message_id"])
            await m.reply(texts.get_text("admin_reply_sent"))
            # نقوم بحذف الرابط بعد استخدامه للحفاظ على نظافة قاعدة البيانات
            database.delete_forward_link(m.reply_to_message.message_id)
        except Exception as e:
            await m.reply(texts.get_text("admin_reply_fail", e=e))

async def callbacks_cmd(cq: types.CallbackQuery, state: FSMContext):
    """Central handler for the main /admin panel callback queries, now database-driven."""
    await cq.answer()
    if await state.get_state() is not None: await state.finish()
    
    d = cq.data
    
    if d == "close_panel": await cq.message.delete(); return
    if d == "back_to_main": 
        await cq.message.edit_text(texts.get_text("admin_panel_title"), reply_markup=create_admin_panel())
        return

    # ✅ تم الإصلاح: منطق حذف آمن وموثوق
    if d.startswith("del_reminder_text_"):
        reminder_text = d.replace("del_reminder_text_", "", 1)
        database.delete_reminder(reminder_text)
        await cq.answer("✅ تم الحذف.", show_alert=True)
        d = "show_reminders" # تحديث العرض

    if d.startswith("del_dyn_reply_key_"):
        keyword = d.replace("del_dyn_reply_key_", "", 1)
        database.delete_dynamic_reply(keyword)
        await cq.answer("✅ تم الحذف.", show_alert=True)
        d = "show_dyn_replies" # تحديث العرض

    if d == "admin_stats":
        # ✅ تم الإصلاح: جلب الإحصائيات مباشرة من قاعدة البيانات بسرعة فائقة
        stats = database.get_db_stats()
        uptime = datetime.datetime.now() - bot.start_time # Assuming bot start time is stored in loader
        stats_text = (f"📊 **إحصائيات البوت:**\n\n"
                      f"📡 الاتصال بالقاعدة: {'✅ متصل' if stats['ok'] else '❌ فشل'}\n"
                      f"👥 إجمالي المستخدمين: {stats['users_count']}\n"
                      f"📖 عناصر المكتبة: {stats['library_count']}\n"
                      f"⏰ المشاركات المجدولة: {stats['scheduled_count']}\n\n"
                      f"⏱️ وقت التشغيل: {uptime}"
                     )
        await cq.message.edit_text(stats_text, reply_markup=back_kb()); return

    if d == "show_reminders":
        # ✅ تم الإصلاح: جلب البيانات مباشرة من قاعدة البيانات
        reminders = database.get_all_reminders()
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        text = "💭 قائمة التذكيرات:\n\nاضغط لحذف تذكير."
        if not reminders: text = "💭 القائمة فارغة."
        else:
            for reminder in reminders:
                # نستخدم النص نفسه في callback data لضمان الحذف الصحيح
                keyboard.add(types.InlineKeyboardButton(f"🗑️ {reminder[:50]}...", callback_data=f"del_reminder_text_{reminder}"))
        keyboard.add(types.InlineKeyboardButton("🔙 العودة", callback_data="admin_reminders"))
        await cq.message.edit_text(text, reply_markup=keyboard)
        return
        
    if d == "show_dyn_replies":
        # ✅ تم الإصلاح: جلب البيانات مباشرة من قاعدة البيانات
        replies = database.get_all_dynamic_replies()
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        text = "💬 قائمة الردود الديناميكية:\n\nاضغط لحذف رد."
        if not replies: text = "💬 القائمة فارغة."
        else:
            for keyword, response in replies.items():
                keyboard.add(types.InlineKeyboardButton(f"🗑️ {keyword} -> {response[:40]}...", callback_data=f"del_dyn_reply_key_{keyword}"))
        keyboard.add(types.InlineKeyboardButton("🔙 العودة", callback_data="admin_dyn_replies"))
        await cq.message.edit_text(text, reply_markup=keyboard)
        return

    # --- FSM Setters remain the same ---
    prompts_and_states = {
        "import_dyn_replies": (texts.get_text("prompt_dyn_replies_file"), AdminStates.waiting_for_dyn_replies_file),
        "import_reminders": (texts.get_text("prompt_reminders_file"), AdminStates.waiting_for_reminders_file),
    }
    menus = {"admin_dyn_replies": texts.get_text("dyn_replies_menu_title"), "admin_reminders": texts.get_text("reminders_menu_title")}
    
    if d in prompts_and_states:
        prompt_text, state_obj = prompts_and_states[d]
        await state.set_state(state_obj)
        await cq.message.edit_text(f"{prompt_text}\n\nلإلغاء العملية، أرسل /cancel."); return

    if d in menus:
        await cq.message.edit_text(menus[d], reply_markup=get_menu_keyboard(d)); return

    standard_prompts = { 
        "add_dyn_reply": (texts.get_text("prompt_dyn_reply_keyword"), AdminStates.waiting_for_dyn_reply_keyword), 
        "add_reminder": (texts.get_text("prompt_reminder_text"), AdminStates.waiting_for_new_reminder),
    }
    if d in standard_prompts:
        prompt_text, state_obj = standard_prompts[d]
        await state.set_state(state_obj)
        await cq.message.edit_text(f"{prompt_text}\n\nلإلغاء العملية، أرسل /cancel."); return

def register_panel_handlers(dp: Dispatcher):
    dp.register_message_handler(admin_panel_cmd, is_admin, commands=['admin'], state="*")
    dp.register_message_handler(admin_reply_cmd, is_admin, is_reply=True, content_types=types.ContentTypes.ANY, state=None)
    dp.register_callback_query_handler(callbacks_cmd, is_admin, state=None)
