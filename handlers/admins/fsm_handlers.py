import io
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
from utils import database, texts
from keyboards.inline.admin_keyboards import create_admin_panel, add_another_kb
from keyboards.inline.advanced_keyboards import create_advanced_panel

def is_admin(message: types.Message):
    return message.from_user.id == ADMIN_CHAT_ID

async def cancel_cmd(m: types.Message, state: FSMContext): 
    if await state.get_state():
        await state.finish()
    await m.reply(texts.get_text("action_cancelled"), reply_markup=create_admin_panel())

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

async def add_reminder_handler(m: types.Message, state: FSMContext):
    reminder_text = m.text.strip()
    database.add_reminder(reminder_text)
    await m.reply(texts.get_text("success_reminder_added"), reply_markup=add_another_kb("add_reminder", "admin_reminders"))
    await state.finish()

async def ban_user_handler(m: types.Message, state: FSMContext):
    try:
        user_id = int(m.text.strip())
        database.ban_user(user_id)
        await m.reply(f"✅ تم حظر المستخدم {user_id} بنجاح.", reply_markup=create_admin_panel())
    except ValueError:
        await m.reply("⚠️ خطأ: الرجاء إرسال ID صحيح (أرقام فقط).")
    await state.finish()

def register_fsm_handlers(dp: Dispatcher):
    dp.register_message_handler(cancel_cmd, is_admin, commands=['cancel'], state='*')
    dp.register_message_handler(dyn_reply_keyword_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_keyword)
    dp.register_message_handler(dyn_reply_content_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_dyn_reply_content)
    dp.register_message_handler(add_reminder_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(ban_user_handler, is_admin, state=AdminStates.waiting_for_ban_id)
