from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
import data_store
from keyboards.inline.admin_keyboards import create_admin_panel, add_another_kb, back_kb

def is_admin(message: types.Message):
    """A filter to check if the user is an admin."""
    return message.from_user.id == ADMIN_CHAT_ID

# --- FSM Handlers ---

async def cancel_cmd(m: types.Message, state: FSMContext): 
    """Handles the /cancel command to exit any state."""
    if await state.get_state() is not None:
        await state.finish()
        await m.reply("✅ تم إلغاء العملية بنجاح.", reply_markup=create_admin_panel())

# --- Dynamic Replies FSM ---

async def dyn_reply_keyword(m: types.Message, state: FSMContext): 
    """Step 1 for adding a dynamic reply: get the keyword."""
    await state.update_data(keyword=m.text.strip())
    await m.reply("👍 ممتاز. الآن أرسل **المحتوى** الذي سيظهر كرد على هذه الكلمة.")
    await AdminStates.next()

async def dyn_reply_content(m: types.Message, state: FSMContext):
    """Step 2 for adding a dynamic reply: get the content."""
    data = await state.get_data()
    keyword, content = data['keyword'], m.text
    data_store.bot_data.setdefault('dynamic_replies', {})[keyword] = content
    data_store.save_data()
    await m.reply(f"✅ **تمت برمجة الرد بنجاح!**\n\n`{keyword}` ⬅️ `{content}`", reply_markup=add_another_kb("add_dyn_reply", "admin_dyn_replies"))
    await state.finish()

async def dyn_reply_delete(m: types.Message, state: FSMContext):
    """Handles deletion of a dynamic reply."""
    keyword = m.text.strip()
    replies = data_store.bot_data.get('dynamic_replies', {})
    if keyword in replies:
        del replies[keyword]
        data_store.save_data()
        await m.reply(f"✅ تم حذف الرد الخاص بالكلمة المفتاحية: `{keyword}`", reply_markup=add_another_kb("delete_dyn_reply", "admin_dyn_replies"))
    else:
        await m.reply("❌ لم يتم العثور على رد بهذا الاسم.", reply_markup=create_admin_panel())
    await state.finish()

# --- Reminders FSM ---

async def add_reminder_text(m: types.Message, state: FSMContext):
    """Handles adding a new reminder."""
    reminder_text = m.text.strip()
    data_store.bot_data.setdefault('reminders', []).append(reminder_text)
    data_store.save_data()
    await m.reply(f"✅ تم إضافة التذكير:\n`{reminder_text}`", reply_markup=add_another_kb("add_reminder", "admin_reminders"))
    await state.finish()

async def delete_reminder_index(m: types.Message, state: FSMContext):
    """Handles deleting a reminder by its index."""
    reminders = data_store.bot_data.get('reminders', [])
    try:
        idx = int(m.text.strip()) - 1
        if 0 <= idx < len(reminders):
            removed = reminders.pop(idx)
            data_store.save_data()
            await m.reply(f"✅ تم حذف التذكير:\n`{removed}`", reply_markup=add_another_kb("delete_reminder", "admin_reminders"))
        else:
            await m.reply(f"❌ رقم غير صالح. الرجاء إرسال رقم بين 1 و {len(reminders)}.")
    except (ValueError, IndexError):
        await m.reply("❌ الرجاء إرسال رقم صحيح.")
    await state.finish()

# --- Ban/Unban FSM ---

async def ban_unban_user(m: types.Message, state: FSMContext, ban: bool):
    """Handles banning and unbanning users by ID."""
    try:
        user_id = int(m.text.strip())
        b_list = data_store.bot_data.setdefault('banned_users', [])
        if ban:
            if user_id not in b_list:
                b_list.append(user_id)
            await m.reply(f"🚫 تم حظر المستخدم `{user_id}` بنجاح.", reply_markup=create_admin_panel())
        else:
            if user_id in b_list:
                b_list.remove(user_id)
                await m.reply(f"✅ تم إلغاء حظر المستخدم `{user_id}` بنجاح.")
            else:
                await m.reply(f"ℹ️ المستخدم `{user_id}` غير محظور أصلاً.")
        data_store.save_data()
    except ValueError:
        await m.reply("❌ ID غير صالح. الرجاء إرسال رقم صحيح.")
    await state.finish()

# --- Channel FSM ---

async def add_channel_msg_text(m: types.Message, state: FSMContext):
    """Handles adding a new channel message."""
    msg_text = m.text.strip()
    data_store.bot_data.setdefault('channel_messages', []).append(msg_text)
    data_store.save_data()
    await m.reply(f"✅ تم إضافة رسالة القناة:\n`{msg_text[:50]}...`", reply_markup=add_another_kb("add_channel_msg", "admin_channel"))
    await state.finish()

async def delete_channel_msg_index(m: types.Message, state: FSMContext):
    """Handles deleting a channel message by its index."""
    messages = data_store.bot_data.get('channel_messages', [])
    try:
        idx = int(m.text.strip()) - 1
        if 0 <= idx < len(messages):
            removed = messages.pop(idx)
            data_store.save_data()
            await m.reply(f"✅ تم حذف رسالة القناة:\n`{removed[:50]}...`", reply_markup=add_another_kb("delete_channel_msg", "admin_channel"))
        else:
            await m.reply(f"❌ رقم غير صالح. الرجاء إرسال رقم بين 1 و {len(messages)}.")
    except (ValueError, IndexError):
        await m.reply("❌ الرجاء إرسال رقم صحيح.")
    await state.finish()

# --- Settings FSM ---

async def set_channel_id_text(m: types.Message, state: FSMContext):
    """Sets the channel ID."""
    channel_id = m.text.strip()
    data_store.bot_data.setdefault('bot_settings', {})['channel_id'] = channel_id
    data_store.save_data()
    await m.reply(f"✅ تم تحديث ID القناة إلى: `{channel_id}`", reply_markup=create_admin_panel())
    await state.finish()

# --- Handler Registration ---

def register_fsm_handlers(dp: Dispatcher):
    """Registers all FSM handlers for the admin."""
    # Register cancel command for all states
    dp.register_message_handler(cancel_cmd, is_admin, commands=['cancel'], state='*')
    
    # Dynamic Replies FSM
    dp.register_message_handler(dyn_reply_keyword, is_admin, state=AdminStates.waiting_for_dyn_reply_keyword)
    dp.register_message_handler(dyn_reply_content, is_admin, state=AdminStates.waiting_for_dyn_reply_content)
    dp.register_message_handler(dyn_reply_delete, is_admin, state=AdminStates.waiting_for_dyn_reply_delete)
    
    # Reminders FSM
    dp.register_message_handler(add_reminder_text, is_admin, state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(delete_reminder_index, is_admin, state=AdminStates.waiting_for_delete_reminder)
    
    # Ban/Unban FSM
    dp.register_message_handler(lambda m, s: ban_unban_user(m, s, True), is_admin, state=AdminStates.waiting_for_ban_id)
    dp.register_message_handler(lambda m, s: ban_unban_user(m, s, False), is_admin, state=AdminStates.waiting_for_unban_id)

    # Channel FSM
    dp.register_message_handler(add_channel_msg_text, is_admin, state=AdminStates.waiting_for_new_channel_msg)
    dp.register_message_handler(delete_channel_msg_index, is_admin, state=AdminStates.waiting_for_delete_channel_msg)
    
    # Settings FSM
    dp.register_message_handler(set_channel_id_text, is_admin, state=AdminStates.waiting_for_channel_id) 
