from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
import datetime
import pytz

from loader import bot
from states.admin_states import AdminStates
import data_store
from keyboards.inline.admin_keyboards import create_admin_panel, add_another_kb
from .panel import is_admin

async def cancel_cmd(m: types.Message, state: FSMContext):
    """Handler to cancel any FSM state."""
    await state.finish()
    await m.reply("✅ تم إلغاء العملية.", reply_markup=create_admin_panel())

async def process_text_input(m: types.Message, state: FSMContext, data_key: list, success_msg: str, is_list=False, kb_info=None):
    """Generic handler for processing simple text inputs."""
    value = m.text.strip()
    target = data_store.bot_data
    for k in data_key[:-1]:
        target = target.setdefault(k, {})
    
    if is_list:
        target.setdefault(data_key[-1], []).append(value)
    else:
        target[data_key[-1]] = value
    
    data_store.save_data()
    reply_markup = add_another_kb(*kb_info) if kb_info else create_admin_panel()
    await m.reply(success_msg.format(value=value), reply_markup=reply_markup)
    await state.finish()

async def process_numeric_input(m: types.Message, state: FSMContext, data_key: list, success_msg: str):
    """Generic handler for processing numeric inputs."""
    try:
        value = int(m.text.strip())
        target = data_store.bot_data
        for k in data_key[:-1]:
            target = target.setdefault(k, {})
        target[data_key[-1]] = value
        data_store.save_data()
        await m.reply(success_msg.format(value=value), reply_markup=create_admin_panel())
    except ValueError:
        await m.reply("❌ الرجاء إرسال رقم صحيح.")
    await state.finish()

async def process_delete_by_index(m: types.Message, state: FSMContext, data_key: str, item_name: str, kb_info: tuple):
    """Generic handler for deleting an item from a list by its index."""
    try:
        idx = int(m.text.strip()) - 1
        lst = data_store.bot_data.get(data_key, [])
        if 0 <= idx < len(lst):
            removed = lst.pop(idx)
            data_store.save_data()
            await m.reply(f"✅ تم حذف {item_name}:\n`{removed}`", reply_markup=add_another_kb(*kb_info))
        else:
            await m.reply(f"❌ رقم غير صالح. الأرقام المتاحة من 1 إلى {len(lst)}")
    except (ValueError, IndexError):
        await m.reply("❌ الرجاء إرسال رقم صحيح من القائمة.")
    await state.finish()

async def ban_unban_user(m: types.Message, state: FSMContext, ban: bool):
    """Handles banning and unbanning users."""
    try:
        user_id = int(m.text.strip())
        b_list = data_store.bot_data['banned_users']
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
        await m.reply("❌ ID غير صالح. الرجاء إرسال رقم فقط.")
    await state.finish()

async def schedule_interval_handler(m: types.Message, state: FSMContext):
    """Handles setting the schedule interval."""
    try:
        hours = float(m.text.strip())
        seconds = int(hours * 3600)
        if seconds < 60:
            await m.reply("❌ أقل فترة مسموح بها هي 0.016 ساعة (دقيقة واحدة).")
        else:
            data_store.bot_data['bot_settings']['schedule_interval_seconds'] = seconds
            data_store.save_data()
            await m.reply(f"✅ تم تحديث فترة النشر التلقائي إلى كل {hours} ساعة.", reply_markup=create_admin_panel())
    except ValueError:
        await m.reply("❌ الرجاء إرسال رقم صحيح. مثال: `24` أو `0.5`.")
    await state.finish()

def register_fsm_handlers(dp: Dispatcher):
    """Registers all FSM handlers for the admin panel."""
    dp.register_message_handler(cancel_cmd, is_admin, commands=['cancel'], state='*')
    
    # Each lambda now correctly accepts both message (m) and state (s)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['reminders'], "✅ تم إضافة التذكير بنجاح.", True, ("add_reminder", "admin_reminders")), is_admin, state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(lambda m, s: process_delete_by_index(m, s, "reminders", "التذكير", ("delete_reminder", "admin_reminders")), is_admin, state=AdminStates.waiting_for_delete_reminder)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['channel_messages'], "✅ تم إضافة رسالة القناة التلقائية بنجاح.", True, ("add_channel_msg", "admin_channel")), is_admin, state=AdminStates.waiting_for_new_channel_msg)
    dp.register_message_handler(lambda m, s: process_delete_by_index(m, s, "channel_messages", "الرسالة", ("delete_channel_msg", "admin_channel")), is_admin, state=AdminStates.waiting_for_delete_channel_msg)
    
    dp.register_message_handler(lambda m, s: ban_unban_user(m, s, True), is_admin, state=AdminStates.waiting_for_ban_id)
    dp.register_message_handler(lambda m, s: ban_unban_user(m, s, False), is_admin, state=AdminStates.waiting_for_unban_id)
    
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['bot_settings', 'channel_id'], "✅ تم تحديث ID القناة بنجاح."), is_admin, state=AdminStates.waiting_for_channel_id)
    dp.register_message_handler(schedule_interval_handler, is_admin, state=AdminStates.waiting_for_schedule_interval)
    
    dp.register_message_handler(lambda m, s: process_numeric_input(m, s, ['bot_settings','spam_message_limit'], "✅ تم تحديث حد الرسائل المسموح به إلى: {value}"), is_admin, state=AdminStates.waiting_for_spam_limit)
    dp.register_message_handler(lambda m, s: process_numeric_input(m, s, ['bot_settings','spam_time_window'], "✅ تم تحديث الفترة الزمنية إلى: {value} ثانية"), is_admin, state=AdminStates.waiting_for_spam_window)
    dp.register_message_handler(lambda m, s: process_numeric_input(m, s, ['bot_settings','slow_mode_seconds'], "✅ تم تحديث فترة التباطؤ إلى: {value} ثانية"), is_admin, state=AdminStates.waiting_for_slow_mode) 
