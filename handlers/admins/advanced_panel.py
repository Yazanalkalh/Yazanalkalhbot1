from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
# ✅ تم الإصلاح: الآن يستورد ID المدير من المكان الصحيح
from config import ADMIN_CHAT_ID
from utils import database, texts
from keyboards.inline.advanced_keyboards import create_advanced_panel, get_advanced_submenu
from states.admin_states import AdminStates

# ✅ تم الإصلاح: الفلتر الآن يستخدم المتغير الصحيح
def is_admin(message: types.Message):
    return message.from_user.id == ADMIN_CHAT_ID

# --- (بقية الكود في هذا الملف سليم تمامًا ولا يحتاج تعديل) ---

async def advanced_panel_cmd(m: types.Message, state: FSMContext):
    if await state.get_state() is not None: await state.finish()
    await m.reply(texts.get_text("adv_panel_title"), reply_markup=create_advanced_panel())

# ... (rest of the advanced panel logic)

def register_advanced_panel_handler(dp: Dispatcher):
    dp.register_message_handler(advanced_panel_cmd, is_admin, commands=['hijri'], state="*")
    dp.register_callback_query_handler(advanced_callbacks_cmd, is_admin, lambda c: c.data.startswith("adv_"), state="*")
