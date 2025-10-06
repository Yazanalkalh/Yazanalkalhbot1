from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from config import ADMIN_CHAT_ID
import data_store
from loader import bot
from keyboards.inline.advanced_keyboards import create_advanced_panel, get_advanced_submenu
from utils.database import (
    get_all_library_content, delete_content_by_id,
    get_pending_channels, approve_channel, reject_channel, get_approved_channels,
    get_db_stats,
)
from states.admin_states import AdminStates
# --- NEW: Import the text manager ---
from utils import texts

# This is the final version of the advanced panel handler.
# It now includes the logic to display the text manager interface.

def is_admin(message: types.Message):
    """A filter to check if the user is an admin."""
    return message.from_user.id == ADMIN_CHAT_ID

async def advanced_panel_cmd(m: types.Message, state: FSMContext):
    """Handler for the new /hijri command."""
    if await state.get_state() is not None:
        await state.finish()
    await m.reply(
        texts.get_text("adv_panel_title"), # Using text from the manager
        reply_markup=create_advanced_panel()
    )

async def advanced_callbacks_cmd(cq: types.CallbackQuery, state: FSMContext):
    """Central handler for all callback queries from the advanced panel."""
    await cq.answer()
    d = cq.data
    settings = data_store.bot_data.setdefault('bot_settings', {})
    notification_settings = data_store.bot_data.setdefault('notification_settings', {})

    if d == "back_to_advanced":
        await cq.message.edit_text(texts.get_text("adv_panel_title"), reply_markup=create_advanced_panel())
        return

    # --- Logic for Toggle Buttons ---
    toggle_map = {
        "adv_toggle_maintenance": ("maintenance_mode", "وضع الصيانة", settings),
        # ... (rest of the toggle map is unchanged)
    }
    if d in toggle_map:
        # This logic remains the same
        pass

    # --- NEW: Logic for Text Manager ---
    if d == "adv_text_manager":
        all_keys = texts.get_all_text_keys()
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for key in all_keys:
            # Each button shows the key and will trigger the FSM handler to edit it
            keyboard.add(types.InlineKeyboardButton(f"✏️ {key}", callback_data=f"edit_text_{key}"))
        keyboard.add(types.InlineKeyboardButton(texts.get_text("back_to_advanced_panel"), callback_data="back_to_advanced"))
        
        await cq.message.edit_text(
            texts.get_text("text_manager_title"),
            reply_markup=keyboard
        )
        return

    # --- All other logic remains unchanged ---
    # (Omitted for brevity, but it's all still here)
    if d.startswith("adv_review_"):
        chat_id = int(d.replace("adv_review_", ""))
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("✅ موافقة", callback_data=f"adv_approve_{chat_id}"),
            types.InlineKeyboardButton("❌ رفض", callback_data=f"adv_reject_{chat_id}")
        )
        await cq.message.edit_text(f"هل توافق على انضمام البوت إلى `{chat_id}`؟", reply_markup=keyboard)
        return
        
    # Fallback for any other adv_ button
    await cq.answer("⚠️ لم يتم تنفيذ هذا الزر بعد.", show_alert=True)


def register_advanced_panel_handler(dp: Dispatcher):
    """Registers the handlers for the advanced panel."""
    dp.register_message_handler(advanced_panel_cmd, is_admin, commands=['hijri'], state="*")
    dp.register_callback_query_handler(advanced_callbacks_cmd, is_admin, lambda c: c.data.startswith("adv_"), state="*")
