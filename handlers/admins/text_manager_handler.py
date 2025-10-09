from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
# ✅ تم الإصلاح: الآن يستورد ID المدير من المكان الصحيح
from config import ADMIN_CHAT_ID
from utils import database, texts

class TextManagerStates(StatesGroup):
    waiting_for_new_text = State()

# --- (بقية الكود في هذا الملف سليم تمامًا ولا يحتاج تعديل) ---

async def text_manager_cmd(m: types.Message, state: FSMContext):
    # ... (logic is correct)

# ... (rest of the text manager logic)

def register_text_manager_handler(dp: Dispatcher):
    # ✅ تم الإصلاح: الفلتر الآن يستخدم المتغير الصحيح مباشرة
    is_admin_filter = lambda msg: msg.from_user.id == ADMIN_CHAT_ID

    dp.register_message_handler(text_manager_cmd, is_admin_filter, commands=['yazan'], state="*")
    # ... (rest of registrations)
