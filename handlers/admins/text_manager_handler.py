from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import data_store
from config import ADMIN_CHAT_ID

# This is a new, completely isolated file for the Royal Text Manager.
# It contains its own states, keyboards, and handlers to be as safe as possible.

# --- 1. The "Dictionary" ---
# A dictionary of all default texts, each with a unique key.
TEXTS = {
    # Main Titles
    "admin_panel_title": "🔧 **لوحة التحكم الإدارية**",
    "adv_panel_title": "🛠️ **لوحة التحكم المتقدمة (غرفة المحركات)**",
    
    # User-Facing Messages
    "user_welcome": "👋 أهلًا وسهلًا بك يا #name!\nأنا هنا لخدمتك.",
    "user_default_reply": "✅ تم استلام رسالتك بنجاح، شكراً لتواصلك.",
    "user_admin_command_warning": "⚠️ <b>تنبيه خاص</b> 👑\n\nهذا الأمر مخصص للمدير فقط 🔒",
    "user_maintenance_mode": "عذرًا، البوت قيد الصيانة حاليًا. سنعود قريباً.",
    "user_force_subscribe": "عذرًا, لاستخدام هذا البوت, يرجى الاشتراك أولاً في قناتنا.",
    "user_anti_duplicate": "لقد استلمت هذه الرسالة منك للتو.",
    
    # Admin Prompts & Replies
    "action_cancelled": "✅ تم إلغاء العملية بنجاح.",
    "prompt_dyn_reply_keyword": "📝 أرسل **الكلمة المفتاحية**:",
    "prompt_dyn_reply_content": "👍 الآن أرسل **المحتوى** للرد.",
    "success_dyn_reply_added": "✅ **تمت برمجة الرد بنجاح!**",
    # ... You can add every single text from the bot here for full control.
}

def get_text(key: str, **kwargs) -> str:
    """The Smart Librarian: gets custom text from DB, or default text if not found."""
    custom_texts = data_store.bot_data.get('custom_texts', {})
    text_template = custom_texts.get(key, TEXTS.get(key, f"_{key}_"))
    return text_template.format(**kwargs)


# --- 2. The "States" needed for this feature ---
class TextManagerStates(StatesGroup):
    waiting_for_new_text = State()


# --- 3. The "Mastermind" (Handlers) ---

async def text_manager_cmd(m: types.Message):
    """Handler for the /yazan command. Displays the text management interface."""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    # Create a button for each editable text
    for key in sorted(TEXTS.keys()):
        keyboard.add(types.InlineKeyboardButton(f"✏️ {key}", callback_data=f"tm_edit_{key}"))
        
    await m.reply("✏️ **مدير النصوص الملكي**\n\nاختر النص الذي تريد تعديله:", reply_markup=keyboard)

async def select_text_to_edit_handler(cq: types.CallbackQuery, state: FSMContext):
    """Handles when the admin selects a text to edit."""
    text_key = cq.data.replace("tm_edit_", "")
    await state.update_data(text_key_to_edit=text_key)
    
    current_text = get_text(text_key)
    prompt = f"النص الحالي لـ `{text_key}` هو:\n\n`{current_text}`\n\nأرسل الآن النص الجديد. يمكنك استخدام تنسيق HTML."
    
    await cq.message.edit_text(prompt)
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
        await m.reply(f"✅ تم تحديث النص `{text_key}` بنجاح.")
    else:
        await m.reply("❌ حدث خطأ، لم يتم العثور على مفتاح النص المطلوب تعديله.")

    await state.finish()

def register_text_manager_handler(dp: Dispatcher):
    """The function to "plug in" our new lamp."""
    # A filter to check if the user is an admin
    is_admin_filter = lambda msg: msg.from_user.id == ADMIN_CHAT_ID

    dp.register_message_handler(text_manager_cmd, is_admin_filter, commands=['yazan'], state="*")
    dp.register_callback_query_handler(select_text_to_edit_handler, is_admin_filter, lambda c: c.data.startswith("tm_edit_"), state="*")
    dp.register_message_handler(process_new_text_handler, is_admin_filter, content_types=types.ContentTypes.ANY, state=TextManagerStates.waiting_for_new_text)
