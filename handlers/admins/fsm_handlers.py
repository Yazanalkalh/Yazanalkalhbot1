from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
import data_store
from keyboards.inline.admin_keyboards import create_admin_panel, add_another_kb
import pytz
import datetime
import asyncio

# This file contains all the logic for handling messages once the bot is in a "waiting state" (FSM).

def is_admin(message: types.Message):
    """A filter to check if the user is an admin."""
    return message.from_user.id == ADMIN_CHAT_ID

# --- Universal Handlers ---
async def cancel_cmd(m: types.Message, state: FSMContext): 
    """Universal cancel handler to exit any state."""
    if await state.get_state() is not None:
        await state.finish()
        await m.reply("✅ تم إلغاء العملية بنجاح.", reply_markup=create_admin_panel())

# --- Dynamic Replies Handlers ---
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

# --- Reminders Handlers ---
async def add_reminder_handler(m: types.Message, state: FSMContext):
    # This function is already correct and working
    reminder_text = m.text.strip()
    data_store.bot_data.setdefault('reminders', []).append(reminder_text)
    data_store.save_data()
    await m.reply("✅ **تمت إضافة التذكير بنجاح!**", reply_markup=add_another_kb("add_reminder", "admin_reminders"))
    await state.finish()

async def delete_reminder_handler(m: types.Message, state: FSMContext):
    # This function is already correct and working
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

# --- THIS IS THE RADICAL FIX: Explicit handlers for each UI customization button ---

async def date_button_label_handler(m: types.Message, state: FSMContext):
    value = m.text.strip()
    data_store.bot_data.setdefault('ui_config', {})['date_button_label'] = value
    data_store.save_data()
    await m.reply(f"✅ تم تحديث اسم زر التاريخ إلى: `{value}`", reply_markup=create_admin_panel())
    await state.finish()

async def time_button_label_handler(m: types.Message, state: FSMContext):
    value = m.text.strip()
    data_store.bot_data.setdefault('ui_config', {})['time_button_label'] = value
    data_store.save_data()
    await m.reply(f"✅ تم تحديث اسم زر الساعة إلى: `{value}`", reply_markup=create_admin_panel())
    await state.finish()

async def reminder_button_label_handler(m: types.Message, state: FSMContext):
    value = m.text.strip()
    data_store.bot_data.setdefault('ui_config', {})['reminder_button_label'] = value
    data_store.save_data()
    await m.reply(f"✅ تم تحديث اسم زر التذكير إلى: `{value}`", reply_markup=create_admin_panel())
    await state.finish()

async def welcome_message_handler(m: types.Message, state: FSMContext):
    value = m.text.strip()
    data_store.bot_data.setdefault('bot_settings', {})['welcome_message'] = value
    data_store.save_data()
    await m.reply(f"✅ تم تحديث رسالة البدء بنجاح.", reply_markup=create_admin_panel())
    await state.finish()

async def reply_message_handler(m: types.Message, state: FSMContext):
    value = m.text.strip()
    data_store.bot_data.setdefault('bot_settings', {})['reply_message'] = value
    data_store.save_data()
    await m.reply(f"✅ تم تحديث رسالة الرد بنجاح.", reply_markup=create_admin_panel())
    await state.finish()

async def set_timezone_handler(m: types.Message, state: FSMContext):
    tz_name = m.text.strip()
    try:
        pytz.timezone(tz_name)
        data_store.bot_data.setdefault('ui_config', {})['timezone'] = tz_name
        data_store.save_data()
        await m.reply(f"✅ تم تحديث المنطقة الزمنية إلى: `{tz_name}`", reply_markup=create_admin_panel())
    except pytz.UnknownTimeZoneError:
        await m.reply("❌ **منطقة زمنية غير صالحة!**\nمثال: `Asia/Aden` أو `Africa/Cairo`")
    await state.finish()

# --- Other handlers (Ban, Channel, etc.) remain the same ---
# (They are omitted here for brevity but are part of the full file)
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
    
# ... other handlers from the previous correct version ...
# (This includes all handlers for Channel, Broadcast, etc.)

# --- Handler Registration ---
def register_fsm_handlers(dp: Dispatcher):
    """Registers all the FSM handlers."""
    # Universal cancel command
    dp.register_message_handler(cancel_cmd, is_admin, commands=['cancel'], state='*')
    
    # Dynamic Replies
    dp.register_message_handler(dyn_reply_keyword_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_keyword)
    dp.register_message_handler(dyn_reply_content_handler, is_admin, content_types=types.ContentTypes.TEXT, state=AdminStates.waiting_for_dyn_reply_content)
    dp.register_message_handler(dyn_reply_delete_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_delete)

    # Reminders
    dp.register_message_handler(add_reminder_handler, is_admin, state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(delete_reminder_handler, is_admin, state=AdminStates.waiting_for_delete_reminder)

    # Ban/Unban
    dp.register_message_handler(ban_user_handler, is_admin, state=AdminStates.waiting_for_ban_id)
    dp.register_message_handler(unban_user_handler, is_admin, state=AdminStates.waiting_for_unban_id)
    
    # --- THIS IS THE FINAL FIX ---
    # Registering the new, explicit handlers for each state. No more confusing lambdas.
    dp.register_message_handler(date_button_label_handler, is_admin, state=AdminStates.waiting_for_date_button_label)
    dp.register_message_handler(time_button_label_handler, is_admin, state=AdminStates.waiting_for_time_button_label)
    dp.register_message_handler(reminder_button_label_handler, is_admin, state=AdminStates.waiting_for_reminder_button_label)
    dp.register_message_handler(set_timezone_handler, is_admin, state=AdminStates.waiting_for_timezone)
    dp.register_message_handler(welcome_message_handler, is_admin, state=AdminStates.waiting_for_welcome_message)
    dp.register_message_handler(reply_message_handler, is_admin, state=AdminStates.waiting_for_reply_message)
    # -----------------------------
    
    # (Registration for other handlers like Channel, Broadcast, etc. remains the same)
    # You would also register handlers for channel messages, broadcast, etc. here if they are not already.
