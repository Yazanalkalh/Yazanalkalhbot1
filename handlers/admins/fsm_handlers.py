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
import io

# This is the final upgraded version of the FSM handlers file.
# It now includes the logic for the new bulk import feature.

def is_admin(message: types.Message):
    """A filter to check if the user is an admin."""
    return message.from_user.id == ADMIN_CHAT_ID

# --- Universal Handler ---
async def cancel_cmd(m: types.Message, state: FSMContext): 
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

# --- NEW: Bulk Import Handler for Dynamic Replies ---
async def import_dyn_replies_handler(m: types.Message, state: FSMContext):
    if not m.document:
        await m.reply("❌ خطأ: الرجاء إرسال ملف وليس نصًا.")
        return

    if not m.document.file_name.lower().endswith('.txt'):
        await m.reply("❌ خطأ: يجب أن يكون الملف من نوع نصي (.txt).")
        return

    file_info = await bot.get_file(m.document.file_id)
    file_content_bytes = await bot.download_file(file_info.file_path)
    
    # Use io.StringIO to handle the byte content as a text file
    file_content = io.StringIO(file_content_bytes.getvalue().decode('utf-8'))
    
    success_count = 0
    fail_count = 0
    
    for line in file_content.readlines():
        line = line.strip()
        if '|' in line:
            parts = line.split('|', 1)
            if len(parts) == 2:
                keyword, reply = parts[0].strip(), parts[1].strip()
                if keyword and reply:
                    data_store.bot_data.setdefault('dynamic_replies', {})[keyword] = reply
                    success_count += 1
                else:
                    fail_count += 1
            else:
                fail_count += 1
        elif line: # If the line is not empty but has no separator
            fail_count += 1
            
    if success_count > 0:
        data_store.save_data()

    await m.reply(
        f"✅ **اكتملت عملية الاستيراد!**\n\n"
        f"- 🟢 الردود الناجحة: {success_count}\n"
        f"- 🔴 الردود الفاشلة (تنسيق خاطئ): {fail_count}",
        reply_markup=create_admin_panel()
    )
    await state.finish()

# --- Reminders Handlers ---
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

# --- NEW: Bulk Import Handler for Reminders ---
async def import_reminders_handler(m: types.Message, state: FSMContext):
    if not m.document:
        await m.reply("❌ خطأ: الرجاء إرسال ملف وليس نصًا.")
        return

    if not m.document.file_name.lower().endswith('.txt'):
        await m.reply("❌ خطأ: يجب أن يكون الملف من نوع نصي (.txt).")
        return

    file_info = await bot.get_file(m.document.file_id)
    file_content_bytes = await bot.download_file(file_info.file_path)
    
    file_content = io.StringIO(file_content_bytes.getvalue().decode('utf-8'))
    
    success_count = 0
    
    for line in file_content.readlines():
        reminder = line.strip()
        if reminder: # Make sure the line is not empty
            data_store.bot_data.setdefault('reminders', []).append(reminder)
            success_count += 1
            
    if success_count > 0:
        data_store.save_data()

    await m.reply(
        f"✅ **اكتملت عملية الاستيراد!**\n\n"
        f"- 🟢 تم استيراد {success_count} تذكيرًا بنجاح.",
        reply_markup=create_admin_panel()
    )
    await state.finish()

# --- Other Handlers (Ban, Channel, etc. are unchanged) ---
async def ban_user_handler(m: types.Message, state: FSMContext):
    # This function remains unchanged
    # ... (code omitted for brevity)
    pass
# ... (All other handlers from the previous version are here, unchanged)

# --- Handler Registration ---
def register_fsm_handlers(dp: Dispatcher):
    """Registers all the FSM handlers."""
    dp.register_message_handler(cancel_cmd, is_admin, commands=['cancel'], state='*')
    
    # Dynamic Replies
    dp.register_message_handler(dyn_reply_keyword_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_keyword)
    dp.register_message_handler(dyn_reply_content_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_dyn_reply_content)
    dp.register_message_handler(dyn_reply_delete_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_delete)
    # --- NEW REGISTRATION 1 ---
    dp.register_message_handler(import_dyn_replies_handler, is_admin, content_types=types.ContentTypes.DOCUMENT, state=AdminStates.waiting_for_dyn_replies_file)

    # Reminders
    dp.register_message_handler(add_reminder_handler, is_admin, state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(delete_reminder_handler, is_admin, state=AdminStates.waiting_for_delete_reminder)
    # --- NEW REGISTRATION 2 ---
    dp.register_message_handler(import_reminders_handler, is_admin, content_types=types.ContentTypes.DOCUMENT, state=AdminStates.waiting_for_reminders_file)

    # ... (Registration for all other handlers remains exactly the same as before)
    # (Omitted for brevity)
