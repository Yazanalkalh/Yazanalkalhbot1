from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import ADMIN_CHAT_ID
from utils import database, texts

def is_admin(message: types.Message):
    return message.from_user.id == ADMIN_CHAT_ID

class TextManagerStates(StatesGroup):
    waiting_for_new_text = State()

async def text_manager_cmd(m: types.Message, state: FSMContext):
    if await state.get_state(): await state.finish()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    all_texts = texts.get_all_text_descriptions()
    for key, description in all_texts:
        keyboard.add(types.InlineKeyboardButton(f"✏️ {description}", callback_data=f"tm_edit_{key}"))
    await m.reply(texts.get_text("text_manager_title"), reply_markup=keyboard)

async def select_text_to_edit_handler(cq: types.CallbackQuery, state: FSMContext):
    await cq.answer()
    text_key = cq.data.replace("tm_edit_", "")
    await state.update_data(text_key_to_edit=text_key)
    current_text = texts.get_text(text_key)
    prompt = texts.get_text("text_manager_prompt_new", text_name=text_key, current_text=current_text)
    await cq.message.edit_text(prompt)
    await TextManagerStates.waiting_for_new_text.set()

async def process_new_text_handler(m: types.Message, state: FSMContext):
    data = await state.get_data()
    text_key = data.get("text_key_to_edit")
    new_text = m.html_text
    if text_key:
        database.update_setting(f"custom_texts.{text_key}", new_text)
        await m.reply(texts.get_text("text_manager_success", text_name=text_key))
    await state.finish()
    # To redisplay the menu
    await text_manager_cmd(m, state)

def register_text_manager_handler(dp: Dispatcher):
    dp.register_message_handler(text_manager_cmd, is_admin, commands=['yazan'], state="*")
    dp.register_callback_query_handler(select_text_to_edit_handler, is_admin, lambda c: c.data.startswith("tm_edit_"), state="*")
    dp.register_message_handler(process_new_text_handler, is_admin, content_types=types.ContentTypes.ANY, state=TextManagerStates.waiting_for_new_text)
