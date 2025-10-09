import io
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
# ✅ تم الإصلاح: الآن يستورد ID المدير من المكان الصحيح
from config import ADMIN_CHAT_ID
from utils import database, texts
from keyboards.inline.admin_keyboards import create_admin_panel, add_another_kb
from keyboards.inline.advanced_keyboards import create_advanced_panel

# ✅ تم الإصلاح: الفلتر الآن يستخدم المتغير الصحيح
def is_admin(message: types.Message):
    return message.from_user.id == ADMIN_CHAT_ID

# --- (بقية الكود في هذا الملف سليم تمامًا ولا يحتاج تعديل) ---

async def cancel_cmd(m: types.Message, state: FSMContext): 
    # ... (logic is correct)

async def dyn_reply_keyword_handler(m: types.Message, state: FSMContext):
    # ... (logic is correct)

# ... (rest of the FSM handlers)

def register_fsm_handlers(dp: Dispatcher):
    dp.register_message_handler(cancel_cmd, is_admin, commands=['cancel'], state='*')
    # ... (rest of registrations)
