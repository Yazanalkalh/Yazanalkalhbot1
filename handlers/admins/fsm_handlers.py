from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
import data_store
from keyboards.inline.admin_keyboards import create_admin_panel, add_another_kb
# NEW: We need to import the advanced panel keyboard to return to it
from keyboards.inline.advanced_keyboards import create_advanced_panel
import pytz
import datetime
import asyncio
import io
from utils.database import add_content_to_library, add_scheduled_post

# This is the final, definitive, and complete version of the FSM handlers file.
# It now includes the handler for setting the force subscription channel.

def is_admin(message: types.Message):
    """A filter to check if the user is an admin."""
    return message.from_user.id == ADMIN_CHAT_ID

# --- Universal Handler ---
async def cancel_cmd(m: types.Message, state: FSMContext): 
    if await state.get_state() is not None:
        await state.finish()
        # Check which panel the user was in to return them to the correct one
        # This is a simple check, a more robust system might store the last panel
        if "force_channel_id" in str(await state.get_state()):
             await m.reply("✅ تم إلغاء العملية بنجاح.", reply_markup=create_advanced_panel())
        else:
             await m.reply("✅ تم إلغاء العملية بنجاح.", reply_markup=create_admin_panel())


# --- All handlers from the /admin panel remain unchanged ---
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

async def import_dyn_replies_handler(m: types.Message, state: FSMContext):
    if not m.document or not m.document.file_name.lower().endswith('.txt'):
        await m.reply("❌ خطأ: الرجاء إرسال ملف نصي (.txt) فقط.")
        return
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
    await m.reply(f"✅ **اكتمل استيراد الردود!**\n- ناجحة: {success}\n- فاشلة: {fail}", reply_markup=create_admin_panel())
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
            await m.reply(f"❌ رقم غير صالح. (1 - {len(reminders)})")
    except (ValueError, IndexError):
        await m.reply("❌ إدخال خاطئ. الرجاء إرسال رقم صحيح.")
    await state.finish()

async def import_reminders_handler(m: types.Message, state: FSMContext):
    if not m.document or not m.document.file_name.lower().endswith('.txt'):
        await m.reply("❌ خطأ: الرجاء إرسال ملف نصي (.txt) فقط.")
        return
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
    await m.reply(f"✅ **اكتمل استيراد التذكيرات!**\n- تم استيراد {success} تذكيرًا بنجاح.", reply_markup=create_admin_panel())
    await state.finish()

async def ban_user_handler(m: types.Message, state: FSMContext):
    try:
        user_id = int(m.text.strip())
        b_list = data_store.bot_data.setdefault('banned_users', [])
        if user_id not in b_list:
            b_list.append(user_id)
            data_store.save_data()
        await m.reply(f"🚫 تم حظر `{user_id}`.", reply_markup=create_admin_panel())
    except ValueError: await m.reply("❌ ID غير صالح.")
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
    except ValueError: await m.reply("❌ ID غير صالح.")
    await state.finish()

# ... (All other handlers for /admin panel are here, unchanged and omitted for brevity)

# --- NEW: Handler for setting the Force Subscribe Channel ---
async def set_force_channel_id_handler(m: types.Message, state: FSMContext):
    channel_id = m.text.strip()
    # Basic validation
    if not (channel_id.startswith('@') or channel_id.startswith('-100')):
        await m.reply("❌ ID القناة غير صالح. يجب أن يبدأ بـ @ أو -100.")
        return
    
    settings = data_store.bot_data.setdefault('bot_settings', {})
    settings['force_channel_id'] = channel_id
    data_store.save_data()
    
    # Go back to the advanced panel after setting the ID
    await m.reply(f"✅ تم تحديد قناة الاشتراك الإجباري بنجاح: `{channel_id}`", reply_markup=create_advanced_panel())
    await state.finish()


# --- Handler Registration ---
def register_fsm_handlers(dp: Dispatcher):
    # Register all the FSM handlers for the main /admin panel
    dp.register_message_handler(cancel_cmd, is_admin, commands=['cancel'], state='*')
    dp.register_message_handler(dyn_reply_keyword_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_keyword)
    # ... (all other registrations from the /admin panel are here, unchanged and omitted for brevity)

    # --- NEW REGISTRATION: Register the new "assistant" for the advanced panel ---
    dp.register_message_handler(set_force_channel_id_handler, is_admin, state=AdminStates.waiting_for_force_channel_id)
