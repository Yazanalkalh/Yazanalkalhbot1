from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
# ✅ تم الإصلاح: الآن يستورد ID المدير من المكان الصحيح
from config import ADMIN_CHAT_ID
from utils import database, texts

class TextManagerStates(StatesGroup):
    waiting_for_new_text = State()

async def text_manager_cmd(m: types.Message, state: FSMContext):
    # This is a placeholder for the full logic
    await m.reply("Text manager opened.")

def register_text_manager_handler(dp: Dispatcher):
    is_admin_filter = lambda msg: msg.from_user.id == ADMIN_CHAT_ID

    dp.register_message_handler(text_manager_cmd, is_admin_filter, commands=['yazan'], state="*")
    # ... (other registrations would go here)
