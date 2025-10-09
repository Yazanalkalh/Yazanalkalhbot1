from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from config import ADMIN_CHAT_ID
from utils import database, texts
from keyboards.inline.advanced_keyboards import create_advanced_panel, get_advanced_submenu
from states.admin_states import AdminStates

def is_admin(message: types.Message):
    return message.from_user.id == ADMIN_CHAT_ID

async def advanced_panel_cmd(m: types.Message, state: FSMContext):
    if await state.get_state() is not None: await state.finish()
    await m.reply(texts.get_text("adv_panel_title"), reply_markup=create_advanced_panel())

async def advanced_callbacks_cmd(cq: types.CallbackQuery, state: FSMContext):
    await cq.answer()
    d = cq.data
    
    if d == "back_to_advanced":
        await cq.message.edit_text(texts.get_text("adv_panel_title"), reply_markup=create_advanced_panel())
        return

    toggle_map = {
        "adv_toggle_maintenance": ("maintenance_mode", "وضع الصيانة"),
        "adv_toggle_antispam": ("anti_duplicate_mode", "منع التكرار"),
    }
    if d in toggle_map:
        key, name = toggle_map[d]
        current_status = database.get_setting(key, False)
        database.update_setting(key, not current_status)
        await cq.message.edit_reply_markup(create_advanced_panel())
        status = "تفعيل" if not current_status else "تعطيل"
        await cq.answer(f"✅ تم {status} {name}.")
        return

    await cq.answer("⚠️ هذه الميزة قيد الإنشاء.", show_alert=True)

def register_advanced_panel_handler(dp: Dispatcher):
    dp.register_message_handler(advanced_panel_cmd, is_admin, commands=['hijri'], state="*")
    dp.register_callback_query_handler(advanced_callbacks_cmd, is_admin, lambda c: c.data.startswith("adv_"), state="*")
