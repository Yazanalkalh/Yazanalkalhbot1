import datetime
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from utils import database, texts
from states.admin_states import AdminStates
from keyboards.inline.admin_keyboards import create_admin_panel, get_menu_keyboard, back_kb

def is_admin(message: types.Message):
    return message.from_user.id == database.ADMIN_CHAT_ID

async def admin_panel_cmd(m: types.Message, state: FSMContext):
    if await state.get_state() is not None:
        await state.finish()
    await m.reply(await texts.get_text("admin_panel_title"), reply_markup=create_admin_panel())

async def admin_reply_cmd(m: types.Message, state: FSMContext):
    if not m.reply_to_message: return
    link = await database.get_forwarded_link(m.reply_to_message.message_id)
    if link:
        try:
            await m.copy_to(link["user_id"], reply_to_message_id=link["original_message_id"])
            await m.reply(await texts.get_text("admin_reply_sent"))
        except Exception as e:
            await m.reply(await texts.get_text("admin_reply_fail", e=e))

async def callbacks_cmd(cq: types.CallbackQuery, state: FSMContext):
    await cq.answer()
    d = cq.data
    
    if d == "close_panel": await cq.message.delete(); return
    if d == "back_to_main": 
        await cq.message.edit_text(await texts.get_text("admin_panel_title"), reply_markup=create_admin_panel())
        return
    
    if d.startswith("del_reminder_text_"):
        reminder_text = cq.data.replace("del_reminder_text_", "")
        await database.delete_reminder(reminder_text)
        await cq.answer("✅ تم الحذف.", show_alert=True)
        d = "show_reminders"

    if d.startswith("del_dyn_reply_key_"):
        keyword = cq.data.replace("del_dyn_reply_key_", "")
        await database.delete_dynamic_reply(keyword)
        await cq.answer("✅ تم الحذف.", show_alert=True)
        d = "show_dyn_replies"

    if d == "admin_stats":
        stats = await database.get_db_stats()
        uptime = datetime.datetime.now() - database.start_time
        stats_text = (f"📊 **إحصائيات البوت:**\n\n"
                      f"👥 المستخدمون: {stats.get('users_count', 0)}\n"
                      f"💭 التذكيرات: {stats.get('reminders_count', 0)}\n"
                      f"📝 الردود: {stats.get('dyn_replies_count', 0)}\n"
                      f"⏱️ وقت التشغيل: {str(uptime).split('.')[0]}")
        await cq.message.edit_text(stats_text, reply_markup=back_kb()); return
    
    prompts_and_states = {
        "import_dyn_replies": (await texts.get_text("prompt_dyn_replies_file"), AdminStates.waiting_for_dyn_replies_file),
        "import_reminders": (await texts.get_text("prompt_reminders_file"), AdminStates.waiting_for_reminders_file),
    }

    menus = {
        "admin_dyn_replies": await texts.get_text("dyn_replies_menu_title"), 
        "admin_reminders": await texts.get_text("reminders_menu_title"),
    }
    
    if d in prompts_and_states:
        prompt_text, state_obj = prompts_and_states[d]
        await state.set_state(state_obj)
        await cq.message.edit_text(f"{prompt_text}\n\nلإلغاء العملية، أرسل /cancel."); return

    if d in menus:
        await cq.message.edit_text(menus[d], reply_markup=get_menu_keyboard(d)); return

    if d == "show_reminders":
        reminders = await database.get_all_reminders()
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        text = "💭 قائمة التذكيرات:\n\nاضغط لحذف تذكير."
        if not reminders: text = "💭 القائمة فارغة."
        else:
            for reminder in reminders:
                keyboard.add(types.InlineKeyboardButton(f"🗑️ {reminder[:50]}...", callback_data=f"del_reminder_text_{reminder}"))
        keyboard.add(types.InlineKeyboardButton("🔙 العودة", callback_data="admin_reminders"))
        await cq.message.edit_text(text, reply_markup=keyboard)
        return

    standard_prompts = { 
        "add_dyn_reply": (await texts.get_text("prompt_dyn_reply_keyword"), AdminStates.waiting_for_dyn_reply_keyword), 
        "delete_dyn_reply": (await texts.get_text("prompt_dyn_reply_delete"), AdminStates.waiting_for_dyn_reply_delete),
        "add_reminder": (await texts.get_text("prompt_reminder_text"), AdminStates.waiting_for_new_reminder),
    }
    if d in standard_prompts:
        prompt_text, state_obj = standard_prompts[d]
        await state.set_state(state_obj)
        await cq.message.edit_text(f"{prompt_text}\n\nلإلغاء العملية، أرسل /cancel."); return

    await cq.answer("⚠️ هذه الميزة قيد الإنشاء.", show_alert=True)

def register_panel_handlers(dp: Dispatcher):
    dp.register_message_handler(admin_panel_cmd, is_admin, commands=['admin'], state="*")
    dp.register_message_handler(admin_reply_cmd, is_admin, is_reply=True, content_types=types.ContentTypes.ANY, state=None)
    dp.register_callback_query_handler(callbacks_cmd, is_admin, lambda c: not c.data.startswith("adv_") and not c.data.startswith("tm_"), state=None)
