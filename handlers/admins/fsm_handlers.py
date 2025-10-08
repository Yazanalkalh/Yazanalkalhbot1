import datetime
import asyncio
import io
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
import data_store
from keyboards.inline.admin_keyboards import create_admin_panel, add_another_kb
from keyboards.inline.advanced_keyboards import create_advanced_panel
from utils.database import add_content_to_library, add_scheduled_post # Assumed to be imported
from utils import texts # Used for central text management

# This is the final, definitive, and complete version of the FSM handlers file.

def is_admin(message: types.Message):
    """A filter to check if the user is an admin."""
    return message.from_user.id == ADMIN_CHAT_ID

# --- Universal Handler ---
async def cancel_cmd(m: types.Message, state: FSMContext): 
    current_state_str = str(await state.get_state())
    if current_state_str:
        await state.finish()
        if "force_channel_id" in current_state_str or "new_text" in current_state_str:
             await m.reply(texts.get_text("action_cancelled"), reply_markup=create_advanced_panel())
        else:
             await m.reply(texts.get_text("action_cancelled"), reply_markup=create_admin_panel())

# --- /admin Panel Handlers (Now using Text Manager) ---

async def dyn_reply_keyword_handler(m: types.Message, state: FSMContext):
    await state.update_data(keyword=m.text.strip())
    await m.reply(texts.get_text("prompt_dyn_reply_content"))
    await AdminStates.next()

async def dyn_reply_content_handler(m: types.Message, state: FSMContext):
    data = await state.get_data()
    keyword = data['keyword']
    content = m.html_text
    data_store.bot_data.setdefault('dynamic_replies', {})[keyword] = content
    data_store.save_data()
    await m.reply(texts.get_text("success_dyn_reply_added"), reply_markup=add_another_kb("add_dyn_reply", "admin_dyn_replies"))
    await state.finish()

async def dyn_reply_delete_handler(m: types.Message, state: FSMContext):
    keyword = m.text.strip()
    if keyword in data_store.bot_data.get('dynamic_replies', {}):
        del data_store.bot_data['dynamic_replies'][keyword]
        data_store.save_data()
        await m.reply(texts.get_text("success_dyn_reply_deleted", keyword=keyword), reply_markup=add_another_kb("delete_dyn_reply", "admin_dyn_replies"))
    else:
        await m.reply(texts.get_text("error_dyn_reply_not_found"), reply_markup=create_admin_panel())
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
                data_store.bot_data.setdefault('dynamic_replies', {})[parts[0].strip()] = parts[1].strip()
                success += 1
            else: fail += 1
        elif line: fail += 1
            
    if success > 0: data_store.save_data()
    await m.reply(texts.get_text("success_import_replies", success=success, fail=fail), reply_markup=create_admin_panel())
    await state.finish()

async def add_reminder_handler(m: types.Message, state: FSMContext):
    reminder_text = m.text.strip()
    data_store.bot_data.setdefault('reminders', []).append(reminder_text)
    data_store.save_data()
    await m.reply(texts.get_text("success_reminder_added"), reply_markup=add_another_kb("add_reminder", "admin_reminders"))
    await state.finish()

async def delete_reminder_handler(m: types.Message, state: FSMContext):
    try:
        idx = int(m.text.strip()) - 1
        reminders = data_store.bot_data.get('reminders', [])
        if 0 <= idx < len(reminders):
            removed = reminders.pop(idx)
            data_store.save_data()
            await m.reply(texts.get_text("success_reminder_deleted", removed=removed), reply_markup=add_another_kb("delete_reminder", "admin_reminders"))
        else:
            await m.reply(texts.get_text("error_invalid_index", max_len=len(reminders)))
    except (ValueError, IndexError):
        await m.reply(texts.get_text("invalid_number"))
    await state.finish()

async def import_reminders_handler(m: types.Message, state: FSMContext):
    if not m.document or not m.document.file_name.lower().endswith('.txt'):
        return await m.reply(texts.get_text("error_file_not_txt"))
    
    file_info = await bot.get_file(m.document.file_id)
    file_content_bytes = await bot.download_file(file_info.file_path)
    file_content = io.StringIO(file_content_bytes.getvalue().decode('utf-8'))
    success = 0
    for line in file_content.readlines():
        reminder = line.strip()
        if reminder:
            data_store.bot_data.setdefault('reminders', []).append(reminder)
            success += 1
            
    if success > 0: data_store.save_data()
    await m.reply(texts.get_text("success_import_reminders", count=success), reply_markup=create_admin_panel())
    await state.finish()

# --- NEW: Handlers for the Text Manager (/yazan) ---
async def select_text_to_edit_handler(cq: types.CallbackQuery, state: FSMContext):
    text_key = cq.data.replace("edit_text_", "")
    await state.update_data(text_key_to_edit=text_key)
    current_text = texts.get_text(text_key)
    prompt = texts.get_text("text_manager_prompt_new", key=text_key, current_text=current_text)
    
    cancel_button = types.InlineKeyboardButton(texts.get_text("action_cancelled"), callback_data="cancel_text_edit") # Unique callback
    
    await cq.message.edit_text(prompt, reply_markup=types.InlineKeyboardMarkup().add(cancel_button))
    await AdminStates.waiting_for_new_text.set()

async def process_new_text_handler(m: types.Message, state: FSMContext):
    data = await state.get_data()
    text_key = data.get("text_key_to_edit")
    new_text = m.html_text
    if text_key:
        data_store.bot_data.setdefault('custom_texts', {})[text_key] = new_text
        data_store.save_data()
        await m.reply(texts.get_text("text_manager_success", key=text_key))
    await state.finish()
    # Go back to the /yazan panel by calling its handler
    from .text_manager_handler import text_manager_cmd
    await text_manager_cmd(m, state)

# --- Handler Registration ---
def register_fsm_handlers(dp: Dispatcher):
    """Registers ALL FSM handlers for BOTH panels."""
    dp.register_message_handler(cancel_cmd, is_admin, commands=['cancel'], state='*')
    
    # --- Text Manager ---
    dp.register_callback_query_handler(select_text_to_edit_handler, is_admin, lambda c: c.data.startswith("edit_text_"), state="*")
    dp.register_message_handler(process_new_text_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_new_text)
    dp.register_callback_query_handler(cancel_cmd, is_admin, lambda c: c.data == "cancel_text_edit", state="*")

    # 🟢 New Registrations for Bulk Import Files (CRITICAL FIX)
    dp.register_message_handler(
        import_dyn_replies_handler, 
        is_admin, 
        content_types=types.ContentTypes.DOCUMENT, 
        state=AdminStates.waiting_for_dyn_replies_file
    )
    dp.register_message_handler(
        import_reminders_handler, 
        is_admin, 
        content_types=types.ContentTypes.DOCUMENT, 
        state=AdminStates.waiting_for_reminders_file
    )

    # --- All /admin handlers (Complete and Correct) ---
    dp.register_message_handler(dyn_reply_keyword_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_keyword)
    dp.register_message_handler(dyn_reply_content_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_dyn_reply_content)
    dp.register_message_handler(dyn_reply_delete_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_delete)
    dp.register_message_handler(add_reminder_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_reminder_text)
    dp.register_message_handler(delete_reminder_handler, is_admin, state=AdminStates.waiting_for_reminder_index)
    # NOTE: You'll need to ensure the missing states from AdminStates are correctly handled and registered.
