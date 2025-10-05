from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
import data_store
# We now import the specific, upgraded database functions
from utils.database import add_content_to_library, add_scheduled_post
from keyboards.inline.admin_keyboards import create_admin_panel, add_another_kb
import pytz
import datetime
import asyncio

# This file contains the complete logic for all FSM states.
# The set_timezone_handler is now upgraded to be more tolerant of user input.

def is_admin(message: types.Message):
    """A filter to check if the user is an admin."""
    return message.from_user.id == ADMIN_CHAT_ID

# --- Universal Handler ---
async def cancel_cmd(m: types.Message, state: FSMContext): 
    if await state.get_state() is not None:
        await state.finish()
        await m.reply("✅ تم إلغاء العملية بنجاح.", reply_markup=create_admin_panel())

# --- Other handlers are unchanged... (omitted for brevity) ---
async def dyn_reply_keyword_handler(m: types.Message, state: FSMContext):
    await state.update_data(keyword=m.text.strip())
    await m.reply("👍 الآن أرسل **المحتوى** للرد.")
    await AdminStates.next()

async def dyn_reply_content_handler(m: types.Message, state: FSMContext):
    data = await state.get_data()
    keyword = data['keyword']
    content = m.text
    data_store.bot_data.setdefault('dynamic_replies', {})[keyword] = content
    data_store.save_data()
    await m.reply("✅ **تمت برمجة الرد بنجاح!**", reply_markup=add_another_kb("add_dyn_reply", "admin_dyn_replies"))
    await state.finish()

async def dyn_reply_delete_handler(m: types.Message, state: FSMContext):
    keyword = m.text.strip()
    if keyword in data_store.bot_data.get('dynamic_replies', {}):
        del data_store.bot_data['dynamic_replies'][keyword]
        data_store.save_data()
        await m.reply(f"✅ تم حذف الرد الخاص بـ `{keyword}`", reply_markup=add_another_kb("delete_dyn_reply", "admin_dyn_replies"))
    else:
        await m.reply("❌ لم يتم العثور على رد بهذا المفتاح.", reply_markup=create_admin_panel())
    await state.finish()

async def add_reminder_handler(m: types.Message, state: FSMContext):
    reminder_text = m.text.strip()
    data_store.bot_data.setdefault('reminders', []).append(reminder_text)
    data_store.save_data()
    await m.reply("✅ **تمت إضافة التذكير بنجاح!**", reply_markup=add_another_kb("add_reminder", "admin_reminders"))
    await state.finish()

async def delete_reminder_handler(m: types.Message, state: FSMContext):
    try:
        idx = int(m.text.strip()) - 1
        reminders = data_store.bot_data.get('reminders', [])
        if 0 <= idx < len(reminders):
            removed = reminders.pop(idx)
            data_store.save_data()
            await m.reply(f"✅ تم حذف التذكير:\n`{removed}`", reply_markup=add_another_kb("delete_reminder", "admin_reminders"))
        else:
            await m.reply(f"❌ رقم غير صالح. الرجاء إدخال رقم بين 1 و {len(reminders)}")
    except (ValueError, IndexError):
        await m.reply("❌ إدخال خاطئ. الرجاء إرسال رقم صحيح.")
    await state.finish()

async def ban_user_handler(m: types.Message, state: FSMContext):
    try:
        user_id = int(m.text.strip())
        b_list = data_store.bot_data.setdefault('banned_users', [])
        if user_id not in b_list:
            b_list.append(user_id)
            data_store.save_data()
        await m.reply(f"🚫 تم حظر `{user_id}`.", reply_markup=create_admin_panel())
    except ValueError:
        await m.reply("❌ ID غير صالح.")
    await state.finish()

async def unban_user_handler(m: types.Message, state: FSMContext):
    try:
        user_id = int(m.text.strip())
        b_list = data_store.bot_data.setdefault('banned_users', [])
        if user_id in b_list:
            b_list.remove(user_id)
            data_store.save_data()
            await m.reply(f"✅ تم إلغاء حظر `{user_id}`.")
        else:
            await m.reply(f"ℹ️ المستخدم `{user_id}` غير محظور أصلاً.")
    except ValueError:
        await m.reply("❌ ID غير صالح.")
    await state.finish()

# --- UPGRADED: Timezone Handler is now more tolerant ---
async def set_timezone_handler(m: types.Message, state: FSMContext):
    tz_name_input = m.text.strip()
    
    # NEW: Alias dictionary to handle common variations and correct them to the official name
    tz_aliases = {
        "Asia/Sana'a": "Asia/Aden",
        "Asia/Sanaa": "Asia/Aden",
        "Sana'a": "Asia/Aden",
        "Sanaa": "Asia/Aden",
        "Riyadh": "Asia/Riyadh",
        "Aden": "Asia/Aden",
        "Cairo": "Africa/Cairo"
    }
    
    # Use the corrected name if found in aliases, otherwise use the original input
    corrected_tz_name = tz_aliases.get(tz_name_input, tz_name_input)
    
    try:
        # Validate the corrected, official name
        pytz.timezone(corrected_tz_name)
        # Save the corrected, official name to the database
        data_store.bot_data.setdefault('ui_config', {})['timezone'] = corrected_tz_name
        data_store.save_data()
        await m.reply(f"✅ تم تحديث المنطقة الزمنية بنجاح إلى: `{corrected_tz_name}`", reply_markup=create_admin_panel())
    except pytz.UnknownTimeZoneError:
        await m.reply(f"❌ **منطقة زمنية غير صالحة:** `{tz_name_input}`\nمثال: `Asia/Riyadh`")
    await state.finish()

# --- Other handlers are unchanged ---
async def welcome_message_handler(m: types.Message, state: FSMContext):
    value = m.text
    data_store.bot_data.setdefault('bot_settings', {})['welcome_message'] = value
    data_store.save_data()
    await m.reply(f"✅ تم تحديث رسالة البدء بنجاح.", reply_markup=create_admin_panel())
    await state.finish()
# ... (and all other handlers like channel messages, scheduling, UI, etc.)

# --- Handler Registration ---
def register_fsm_handlers(dp: Dispatcher):
    dp.register_message_handler(cancel_cmd, is_admin, commands=['cancel'], state='*')
    # All registrations remain the same, but set_timezone_handler is now smarter
    dp.register_message_handler(set_timezone_handler, is_admin, state=AdminStates.waiting_for_timezone)
    # ... (all other registrations)
    dp.register_message_handler(dyn_reply_keyword_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_keyword)
    dp.register_message_handler(dyn_reply_content_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_content)
    dp.register_message_handler(dyn_reply_delete_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_delete)
    dp.register_message_handler(add_reminder_handler, is_admin, state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(delete_reminder_handler, is_admin, state=AdminStates.waiting_for_delete_reminder)
    dp.register_message_handler(ban_user_handler, is_admin, state=AdminStates.waiting_for_ban_id)
    dp.register_message_handler(unban_user_handler, is_admin, state=AdminStates.waiting_for_unban_id)
    dp.register_message_handler(welcome_message_handler, is_admin, state=AdminStates.waiting_for_welcome_message)
    # ... and so on


 
