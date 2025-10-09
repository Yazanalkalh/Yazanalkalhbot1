import asyncio
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from config import ADMIN_CHAT_ID
from utils import database, texts
from states.admin_states import AdminStates
from keyboards.inline.admin_keyboards import create_admin_panel, get_broadcast_confirmation_kb

def is_admin(message: types.Message):
    return message.from_user.id == ADMIN_CHAT_ID

# Universal cancel handler
async def cancel_fsm(m: types.Message, state: FSMContext):
    if await state.get_state() is not None:
        await state.finish()
    await m.reply(texts.get_text("action_cancelled"), reply_markup=create_admin_panel())

# Reminder Handlers
async def process_new_reminder(m: types.Message, state: FSMContext):
    database.add_reminder(m.text)
    await m.reply("✅ تم إضافة التذكير بنجاح.", reply_markup=create_admin_panel())
    await state.finish()

# Ban/Unban Handlers
async def process_ban_id(m: types.Message, state: FSMContext):
    try:
        user_id = int(m.text.strip())
        database.ban_user(user_id)
        await m.reply(f"🚫 تم حظر المستخدم `{user_id}`.", reply_markup=create_admin_panel())
    except ValueError:
        await m.reply("⚠️ خطأ. الرجاء إرسال ID رقمي صحيح.")
    await state.finish()

async def process_unban_id(m: types.Message, state: FSMContext):
    try:
        user_id = int(m.text.strip())
        database.unban_user(user_id)
        await m.reply(f"✅ تم إلغاء حظر المستخدم `{user_id}`.", reply_markup=create_admin_panel())
    except ValueError:
        await m.reply("⚠️ خطأ. الرجاء إرسال ID رقمي صحيح.")
    await state.finish()

# Broadcast Handlers
async def process_broadcast_message(m: types.Message, state: FSMContext):
    user_ids = database.get_all_user_ids()
    await state.update_data(user_ids=user_ids)
    
    confirmation_text = texts.get_text("broadcast_confirm", count=len(user_ids))
    # We send the confirmation request as a reply to the message to be broadcasted
    await m.reply(confirmation_text, reply_markup=get_broadcast_confirmation_kb())
    await AdminStates.confirm_broadcast.set()


def register_fsm_handlers(dp: Dispatcher):
    dp.register_message_handler(cancel_fsm, is_admin, commands=['cancel'], state='*')
    
    dp.register_message_handler(process_new_reminder, is_admin, state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(process_ban_id, is_admin, state=AdminStates.waiting_for_ban_id)
    dp.register_message_handler(process_unban_id, is_admin, state=AdminStates.waiting_for_unban_id)
    dp.register_message_handler(process_broadcast_message, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_broadcast_message)
