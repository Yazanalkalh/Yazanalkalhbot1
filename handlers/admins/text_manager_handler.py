from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import data_store
from config import ADMIN_CHAT_ID

# --- NEW: We now import everything from our central "Smart Dictionary" ---
from utils.texts import get_text, get_all_text_descriptions

# This is the upgraded, isolated file for the Royal Text Manager.
# It now uses the central texts.py file to build its interface.

# --- The "States" now live here to keep the file self-contained ---
class TextManagerStates(StatesGroup):
    waiting_for_new_text = State()

# --- The "Mastermind" (Handlers) ---

async def text_manager_cmd(m: types.Message, state: FSMContext):
    """
    Handler for the /yazan command. 
    UPGRADED: It now uses the descriptions from the smart dictionary to build the buttons.
    """
    if await state.get_state():
        await state.finish()
        
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    # Get the list of (key, description) tuples from our smart dictionary
    all_texts = get_all_text_descriptions()
    
    # Create a button for each text, using the Arabic description
    for key, description in all_texts:
        keyboard.add(types.InlineKeyboardButton(f"✏️ {description}", callback_data=f"tm_edit_{key}"))
        
    await m.reply(get_text("text_manager_title"), reply_markup=keyboard)

async def select_text_to_edit_handler(cq: types.CallbackQuery, state: FSMContext):
    """Handles when the admin selects a text to edit."""
    await cq.answer()
    text_key = cq.data.replace("tm_edit_", "")
    await state.update_data(text_key_to_edit=text_key)
    
    current_text = get_text(text_key)
    prompt = get_text("text_manager_prompt_new", key=text_key, current_text=current_text)
    
    # Create a cancel button that uses the text from our dictionary
    cancel_button = types.InlineKeyboardButton(get_text("action_cancelled"), callback_data="tm_cancel")
    
    await cq.message.edit_text(prompt, reply_markup=types.InlineKeyboardMarkup().add(cancel_button))
    await TextManagerStates.waiting_for_new_text.set()

async def process_new_text_handler(m: types.Message, state: FSMContext):
    """Handles the message with the new text."""
    data = await state.get_data()
    text_key = data.get("text_key_to_edit")
    
    # Use html_text to preserve any formatting like bold or links
    new_text = m.html_text
    
    if text_key:
        # Save the new text in our "special notes" (the database)
        data_store.bot_data.setdefault('custom_texts', {})[text_key] = new_text
        data_store.save_data()
        await m.reply(get_text("text_manager_success", key=text_key))
    else:
        # This case should ideally not happen
        await m.reply("❌ حدث خطأ، لم يتم العثور على مفتاح النص المطلوب تعديله.")

    await state.finish()
    # Show the main text manager menu again for convenience
    await text_manager_cmd(m)

async def cancel_text_manager(cq: types.CallbackQuery, state: FSMContext):
    """Handles cancellation within the text manager."""
    await cq.answer()
    await state.finish()
    # Go back to the main text manager menu instead of just deleting
    await cq.message.edit_text(get_text("action_cancelled"))
    await text_manager_cmd(cq.message)


def register_text_manager_handler(dp: Dispatcher):
    """The function to "plug in" our new, isolated feature."""
    is_admin_filter = lambda msg: msg.from_user.id == ADMIN_CHAT_ID

    dp.register_message_handler(text_manager_cmd, is_admin_filter, commands=['yazan'], state="*")
    dp.register_callback_query_handler(select_text_to_edit_handler, is_admin_filter, lambda c: c.data.startswith("tm_edit_"), state="*")
    dp.register_message_handler(process_new_text_handler, is_admin_filter, content_types=types.ContentTypes.ANY, state=TextManagerStates.waiting_for_new_text)
    dp.register_callback_query_handler(cancel_text_manager, is_admin_filter, lambda c: c.data == "tm_cancel", state="*")
