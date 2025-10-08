from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import data_store
from config import ADMIN_CHAT_ID
# --- Correctly import from the central dictionary ---
from utils.texts import get_text, get_all_text_descriptions

# This is the final, definitive, and corrected version of the Royal Text Manager.

class TextManagerStates(StatesGroup):
    waiting_for_new_text = State()

async def text_manager_cmd(m: types.Message, state: FSMContext):
    """Handler for the /yazan command. Displays the text management interface."""
    if await state.get_state():
        await state.finish()
        
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    all_texts = get_all_text_descriptions()
    
    for key, description in all_texts:
        keyboard.add(types.InlineKeyboardButton(f"✏️ {description}", callback_data=f"tm_edit_{key}"))
        
    await m.reply(get_text("text_manager_title"), reply_markup=keyboard)

async def select_text_to_edit_handler(cq: types.CallbackQuery, state: FSMContext):
    """Handles when the admin selects a text to edit."""
    await cq.answer()
    text_key = cq.data.replace("tm_edit_", "")
    await state.update_data(text_key_to_edit=text_key)
    
    current_text = get_text(text_key)
    
    # --- THIS IS THE FIX ---
    # The function call is now correct, using 'text_name' as the placeholder.
    prompt = get_text("text_manager_prompt_new", text_name=text_key, current_text=current_text)
    
    cancel_button = types.InlineKeyboardButton(get_text("action_cancelled"), callback_data="tm_cancel")
    
    await cq.message.edit_text(prompt, reply_markup=types.InlineKeyboardMarkup().add(cancel_button))
    await TextManagerStates.waiting_for_new_text.set()

async def process_new_text_handler(m: types.Message, state: FSMContext):
    """Handles the message with the new text."""
    data = await state.get_data()
    text_key = data.get("text_key_to_edit")
    new_text = m.html_text
    
    if text_key:
        data_store.bot_data.setdefault('custom_texts', {})[text_key] = new_text
        data_store.save_data()
        # --- THIS IS THE FIX ---
        await m.reply(get_text("text_manager_success", text_name=text_key))
    
    await state.finish()
    await text_manager_cmd(m) # Show the main menu again

async def cancel_text_manager(cq: types.CallbackQuery, state: FSMContext):
    """Handles cancellation within the text manager."""
    await cq.answer()
    await state.finish()
    await cq.message.delete()
    await cq.bot.send_message(cq.from_user.id, get_text("action_cancelled"))

def register_text_manager_handler(dp: Dispatcher):
    """Plugs in the new, isolated feature."""
    is_admin_filter = lambda msg: msg.from_user.id == ADMIN_CHAT_ID

    dp.register_message_handler(text_manager_cmd, is_admin_filter, commands=['yazan'], state="*")
    dp.register_callback_query_handler(select_text_to_edit_handler, is_admin_filter, lambda c: c.data.startswith("tm_edit_"), state="*")
    dp.register_message_handler(process_new_text_handler, is_admin_filter, content_types=types.ContentTypes.ANY, state=TextManagerStates.waiting_for_new_text)
    dp.register_callback_query_handler(cancel_text_manager, is_admin_filter, lambda c: c.data == "tm_cancel", state="*")
