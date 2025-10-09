import datetime
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from config import ADMIN_CHAT_ID
from utils import database, texts
from states.admin_states import AdminStates
from keyboards.inline.admin_keyboards import (
    create_admin_panel, get_reminders_menu, get_ban_menu, 
    back_to_main_kb, get_broadcast_confirmation_kb
)

def is_admin(message: types.Message):
    return message.from_user.id == ADMIN_CHAT_ID

# --- Main Command and Navigation ---
async def admin_panel_cmd(m: types.Message, state: FSMContext):
    if await state.get_state() is not None:
        await state.finish()
    await m.reply(texts.get_text("admin_panel_title"), reply_markup=create_admin_panel())

async def admin_callbacks_handler(cq: types.CallbackQuery, state: FSMContext):
    await cq.answer()
    d = cq.data
    
    if d == "close_panel": await cq.message.delete(); return
    if d == "back_to_main":
        await cq.message.edit_text(texts.get_text("admin_panel_title"), reply_markup=create_admin_panel())
        return

    # --- Menu Navigation ---
    if d == "menu_reminders":
        await cq.message.edit_text("اختر إجراءً للتذكيرات:", reply_markup=get_reminders_menu())
        return
    if d == "menu_ban":
        await cq.message.edit_text("اختر إجراءً للحظر:", reply_markup=get_ban_menu())
        return

    # --- Actions that start an FSM state ---
    if d == "add_reminder":
        await cq.message.edit_text("أرسل الآن نص التذكير الجديد. لإلغاء العملية، أرسل /cancel.")
        await AdminStates.waiting_for_new_reminder.set()
        return
    if d == "ban_user":
        await cq.message.edit_text("أرسل الآن ID المستخدم الذي تريد حظره.")
        await AdminStates.waiting_for_ban_id.set()
        return
    if d == "unban_user":
        await cq.message.edit_text("أرسل الآن ID المستخدم الذي تريد إلغاء حظره.")
        await AdminStates.waiting_for_unban_id.set()
        return
    if d == "broadcast":
        await cq.message.edit_text(texts.get_text("broadcast_prompt"))
        await AdminStates.waiting_for_broadcast_message.set()
        return

    # --- Other Actions ---
    if d == "admin_stats":
        stats = database.get_db_stats()
        uptime = datetime.datetime.now() - database.start_time
        stats_text = (f"📊 **إحصائيات البوت:**\n\n"
                      f"👥 المستخدمون: {stats.get('users_count', 0)}\n"
                      f"🚫 المحظورون: {stats.get('banned_count', 0)}\n"
                      f"💭 التذكيرات: {stats.get('reminders_count', 0)}\n"
                      f"⏱️ وقت التشغيل: {str(uptime).split('.')[0]}")
        await cq.message.edit_text(stats_text, reply_markup=back_to_main_kb())
        return
    
    if d == "confirm_broadcast":
        data = await state.get_data()
        user_ids = data.get("user_ids", [])
        await state.finish()
        await cq.message.edit_text(texts.get_text("broadcast_started"))
        
        success, fail = 0, 0
        for user_id in user_ids:
            try:
                await cq.message.copy_to(user_id)
                success += 1
            except Exception:
                fail += 1
            await asyncio.sleep(0.1) # Avoid hitting Telegram limits
        
        await cq.message.answer(texts.get_text("broadcast_complete", success=success, fail=fail))
        return

    if d == "cancel_broadcast":
        await state.finish()
        await cq.message.edit_text("تم إلغاء النشر.", reply_markup=create_admin_panel())
        return

# --- Handler for replies to forwarded messages ---
async def admin_reply_handler(m: types.Message):
    if not m.reply_to_message: return
    link = database.get_forwarded_link(m.reply_to_message.message_id)
    if link:
        try:
            await m.copy_to(link["user_id"], reply_to_message_id=link["original_message_id"])
            await m.reply(texts.get_text("admin_reply_sent"))
        except Exception as e:
            await m.reply(texts.get_text("admin_reply_fail", e=e))

# --- Registration ---
def register_panel_handlers(dp: Dispatcher):
    dp.register_message_handler(admin_panel_cmd, is_admin, commands=['admin'], state="*")
    dp.register_message_handler(admin_reply_handler, is_admin, is_reply=True, content_types=types.ContentTypes.ANY, state=None)
    dp.register_callback_query_handler(admin_callbacks_handler, is_admin, state="*")
