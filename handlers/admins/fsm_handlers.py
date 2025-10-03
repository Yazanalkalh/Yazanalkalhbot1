from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
import data_store
from keyboards.inline.admin_keyboards import create_admin_panel, add_another_kb
import datetime
import pytz

# --- This is a simple, correct filter that works with states ---
def is_admin(message: types.Message):
    return message.from_user.id == ADMIN_CHAT_ID

# --- FSM Handlers ---
async def cancel_cmd(m: types.Message, state: FSMContext): 
    await state.finish()
    await m.reply("✅ تم إلغاء العملية.", reply_markup=create_admin_panel())

async def dyn_reply_keyword(m: types.Message, state: FSMContext): 
    await state.update_data(keyword=m.text.strip())
    await m.reply("👍 الآن أرسل **المحتوى** للرد.")
    await AdminStates.next()

async def dyn_reply_content(m: types.Message, state: FSMContext):
    data = await state.get_data()
    keyword, content = data['keyword'], m.text
    data_store.bot_data['dynamic_replies'][keyword] = content
    data_store.save_data()
    await m.reply("✅ **تمت برمجة الرد بنجاح!**", reply_markup=add_another_kb("add_dyn_reply", "admin_dyn_replies"))
    await state.finish()

async def dyn_reply_delete(m: types.Message, state: FSMContext):
    keyword = m.text.strip()
    if keyword in data_store.bot_data['dynamic_replies']:
        del data_store.bot_data['dynamic_replies'][keyword]
        data_store.save_data()
        await m.reply(f"✅ تم حذف الرد الخاص بـ `{keyword}`", reply_markup=add_another_kb("delete_dyn_reply", "admin_dyn_replies"))
    else:
        await m.reply("❌ لم يتم العثور على رد بهذا الاسم.", reply_markup=create_admin_panel())
    await state.finish()

# --- Generic Handlers for different input types ---

async def process_text_input(m: types.Message, state: FSMContext, data_key: list, success_msg: str, is_list=False, kb_info=None):
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

async def process_delete_by_index(m: types.Message, state: FSMContext, data_key: str, item_name: str, kb_info: tuple):
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
        await m.reply("❌ ID غير صالح. الرجاء إرسال رقم صحيح.")
    await state.finish()
    
# --- Handler Registration ---

def register_fsm_handlers(dp: Dispatcher):
    # Register cancel command for all states
    dp.register_message_handler(cancel_cmd, is_admin, commands=['cancel'], state='*')
    
    # Dynamic Replies
    dp.register_message_handler(dyn_reply_keyword, is_admin, state=AdminStates.waiting_for_dyn_reply_keyword)
    dp.register_message_handler(dyn_reply_content, is_admin, state=AdminStates.waiting_for_dyn_reply_content)
    dp.register_message_handler(dyn_reply_delete, is_admin, state=AdminStates.waiting_for_dyn_reply_delete)
    
    # Reminders
    dp.register_message_handler(
        lambda m, s: process_text_input(m, s, ['reminders'], "✅ تم إضافة التذكير بنجاح.", True, ("add_reminder", "admin_reminders")),
        is_admin, state=AdminStates.waiting_for_new_reminder
    )
    dp.register_message_handler(
        lambda m, s: process_delete_by_index(m, s, "reminders", "التذكير", ("delete_reminder", "admin_reminders")),
        is_admin, state=AdminStates.waiting_for_delete_reminder
    )
    
    # Channel Messages
    dp.register_message_handler(
        lambda m, s: process_text_input(m, s, ['channel_messages'], "✅ تم إضافة رسالة القناة بنجاح.", True, ("add_channel_msg", "admin_channel")),
        is_admin, state=AdminStates.waiting_for_new_channel_msg
    )
    dp.register_message_handler(
        lambda m, s: process_delete_by_index(m, s, "channel_messages", "الرسالة", ("delete_channel_msg", "admin_channel")),
        is_admin, state=AdminStates.waiting_for_delete_channel_msg
    )
    
    # Ban Management
    dp.register_message_handler(
        lambda m, s: ban_unban_user(m, s, True), 
        is_admin, state=AdminStates.waiting_for_ban_id
    )
    dp.register_message_handler(
        lambda m, s: ban_unban_user(m, s, False), 
        is_admin, state=AdminStates.waiting_for_unban_id
    )

    # Channel Settings
    dp.register_message_handler(
        lambda m, s: process_text_input(m, s, ['bot_settings', 'channel_id'], "✅ تم تحديث ID القناة إلى: {value}"),
        is_admin, state=AdminStates.waiting_for_channel_id
    ) 
