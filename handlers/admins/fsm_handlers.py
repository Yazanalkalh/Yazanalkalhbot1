import io
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
# ✅ تم الإصلاح: الآن يستورد ID المدير من المكان الصحيح
from config import ADMIN_CHAT_ID
from utils import database, texts
from keyboards.inline.admin_keyboards import create_admin_panel, add_another_kb
from keyboards.inline.advanced_keyboards import create_advanced_panel

# ✅ تم الإصلاح: الفلتر الآن يستخدم المتغير الصحيح
def is_admin(message: types.Message):
    return message.from_user.id == ADMIN_CHAT_ID

# --- Universal Handler ---
async def cancel_cmd(m: types.Message, state: FSMContext): 
    current_state_str = str(await state.get_state())
    if current_state_str:
        await state.finish()
        cancel_text = texts.get_text("action_cancelled")
        # Note: create_advanced_panel is not async, so we don't await it
        if "force_channel_id" in current_state_str or "new_text" in current_state_str:
             await m.reply(cancel_text, reply_markup=create_advanced_panel())
        else:
             await m.reply(cancel_text, reply_markup=create_admin_panel())

# --- /admin Panel Handlers ---
async def dyn_reply_keyword_handler(m: types.Message, state: FSMContext):
    await state.update_data(keyword=m.text.strip())
    await m.reply(texts.get_text("prompt_dyn_reply_content"))
    await AdminStates.next()

async def dyn_reply_content_handler(m: types.Message, state: FSMContext):
    data = await state.get_data()
    keyword = data['keyword']
    content = m.html_text
    database.update_setting(f"dynamic_replies.{keyword}", content)
    await m.reply(texts.get_text("success_dyn_reply_added"), reply_markup=add_another_kb("add_dyn_reply", "admin_dyn_replies"))
    await state.finish()

async def dyn_reply_delete_handler(m: types.Message, state: FSMContext):
    keyword = m.text.strip()
    # We now need a way to delete a specific key from the dict in the DB
    # For now, we assume a function for this exists or will be added.
    database.delete_dynamic_reply(keyword) # Assuming this function is in database.py
    await m.reply(texts.get_text("success_dyn_reply_deleted", keyword=keyword), reply_markup=add_another_kb("delete_dyn_reply", "admin_dyn_replies"))
    await state.finish()

async def import_dyn_replies_handler(m: types.Message, state: FSMContext):
    if not m.document or not m.document.file_name.lower().endswith('.txt'):
        return await m.reply(texts.get_text("error_file_not_txt"))
    
    file_info = await bot.get_file(m.document.file_id)
    file_content_bytes = await bot.download_file(file_info.file_path)
    file_content = io.StringIO(file_content_bytes.getvalue().decode('utf-8'))
    
    success, fail = 0, 0
    for line in file_content.readlines():
        line = line.strip()
        if '|' in line:
            parts = line.split('|', 1)
            if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                database.update_setting(f"dynamic_replies.{parts[0].strip()}", parts[1].strip())
                success += 1
            else: fail += 1
        elif line: fail += 1
            
    await m.reply(texts.get_text("success_import_replies", success=success, fail=fail), reply_markup=create_admin_panel())
    await state.finish()

async def add_reminder_handler(m: types.Message, state: FSMContext):
    reminder_text = m.text.strip()
    database.add_reminder(reminder_text) # Assuming this function is in database.py
    await m.reply(texts.get_text("success_reminder_added"), reply_markup=add_another_kb("add_reminder", "admin_reminders"))
    await state.finish()

async def import_reminders_handler(m: types.Message, state: FSMContext):
    if not m.document or not m.document.file_name.lower().endswith('.txt'):
        return await m.reply(texts.get_text("error_file_not_txt"))
    
    file_info = await bot.get_file(m.document.file_id)
    file_content_bytes = await bot.download_file(file_info.file_path)
    file_content = io.StringIO(file_content_bytes.getvalue().decode('utf-8'))
    
    reminders_to_add = [line.strip() for line in file_content.readlines() if line.strip()]
            
    if reminders_to_add:
        database.bulk_add_reminders(reminders_to_add) # Assuming this function is in database.py

    await m.reply(texts.get_text("success_import_reminders", count=len(reminders_to_add)), reply_markup=create_admin_panel())
    await state.finish()

# --- Handler Registration (This part is correct) ---
def register_fsm_handlers(dp: Dispatcher):
    dp.register_message_handler(cancel_cmd, is_admin, commands=['cancel'], state='*')
    dp.register_message_handler(import_dyn_replies_handler, is_admin, content_types=types.ContentTypes.DOCUMENT, state=AdminStates.waiting_for_dyn_replies_file)
    dp.register_message_handler(import_reminders_handler, is_admin, content_types=types.ContentTypes.DOCUMENT, state=AdminStates.waiting_for_reminders_file)
    dp.register_message_handler(dyn_reply_keyword_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_keyword)
    dp.register_message_handler(dyn_reply_content_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_dyn_reply_content)
    dp.register_message_handler(dyn_reply_delete_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_delete)
    dp.register_message_handler(add_reminder_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_new_reminder)
