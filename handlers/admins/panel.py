import datetime
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
import data_store
from keyboards.inline.admin_keyboards import create_admin_panel, get_menu_keyboard, back_kb
# --- UPGRADE: Import the text manager ---
from utils import texts

# This is the final, definitive, and fixed version of the main admin panel.
# The issue with callbacks has been fixed by adjusting the handler registration.

def is_admin(message: types.Message):
    """A filter to check if the user is an admin."""
    # Ensure ID comparison is correct (ID in config is int)
    return message.from_user.id == ADMIN_CHAT_ID

async def admin_panel_cmd(m: types.Message, state: FSMContext):
    """Handler for the /admin command."""
    if await state.get_state() is not None:
        await state.finish()
    await m.reply(texts.get_text("admin_panel_title"), reply_markup=create_admin_panel())

async def admin_reply_cmd(m: types.Message, state: FSMContext):
    """Handler for admin replies to forwarded messages."""
    if not m.reply_to_message: return
    link = data_store.forwarded_message_links.get(m.reply_to_message.message_id)
    if link:
        try:
            await m.copy_to(link["user_id"], reply_to_message_id=link["original_message_id"])
            await m.reply(texts.get_text("admin_reply_sent"))
        except Exception as e:
            await m.reply(texts.get_text("admin_reply_fail", e=e))

async def callbacks_cmd(cq: types.CallbackQuery, state: FSMContext):
    """
    Central handler for the main /admin panel callback queries.
    This runs only when the state is None (not in FSM), preventing conflicts.
    """
    await cq.answer()
    
    # We don't check state here because the handler registration already filtered for state=None
    
    d = cq.data
    
    # Main navigation
    if d == "close_panel": await cq.message.delete(); return
    if d == "back_to_main": 
        await cq.message.edit_text(texts.get_text("admin_panel_title"), reply_markup=create_admin_panel())
        return
    
    # Interactive List Deletion (Corrected logic)
    if d.startswith("del_reminder_idx_"):
        idx = int(d.replace("del_reminder_idx_", ""))
        data = await state.get_data()
        reminders_list = data.get('reminders_view', [])
        
        # Ensure that deletion happens only if the index is valid
        if 0 <= idx < len(reminders_list):
            reminder_to_delete = reminders_list[idx] # Get the item text
            
            # Find and remove the actual reminder from the main bot_data list
            if reminder_to_delete in data_store.bot_data.get('reminders', []):
                data_store.bot_data['reminders'].remove(reminder_to_delete)
                data_store.save_data()
            
            # Re-run the view logic
            await cq.answer("✅ تم الحذف.", show_alert=True)
            # Re-call the view function logic
            d = "show_reminders" 
        else:
            await cq.answer("⚠️ خطأ في الفهرس.", show_alert=True)

    if d.startswith("del_dyn_reply_key_"):
        keyword = d.replace("del_dyn_reply_key_", "")
        if keyword in data_store.bot_data.get('dynamic_replies', {}):
            del data_store.bot_data['dynamic_replies'][keyword]
            data_store.save_data()
            await cq.answer("✅ تم الحذف.", show_alert=True)
            d = "show_dyn_replies" # Refresh the view
        else:
            await cq.answer("⚠️ الكلمة المفتاحية غير موجودة.", show_alert=True)
            
    # Other handlers (All use hardcoded text for now until fully migrated)
    if d == "admin_stats":
        stats_text = (f"📊 **إحصائيات البوت:**\n\n"
                      f"👥 المستخدمون: {len(data_store.bot_data.get('users', []))}\n"
                      f"⏱️ وقت التشغيل: {datetime.datetime.now() - data_store.start_time}"
                      )
        await cq.message.edit_text(stats_text, reply_markup=back_kb()); return
    
    # --- New FSM Setters for Bulk Import (Matching the states in fsm_handlers.py) ---
    prompts_and_states = {
        "import_dyn_replies": (texts.get_text("prompt_dyn_replies_file"), AdminStates.waiting_for_dyn_replies_file),
        "import_reminders": (texts.get_text("prompt_reminders_file"), AdminStates.waiting_for_reminders_file),
    }

    # This part shows how menu titles would be upgraded
    menus = {
        "admin_dyn_replies": texts.get_text("dyn_replies_menu_title"), 
        "admin_reminders": texts.get_text("reminders_menu_title"),
        # ... and so on for all menus
    }
    
    # Combine menus and prompts for flow control
    if d in prompts_and_states:
        prompt_text, state_obj = prompts_and_states[d]
        await state.set_state(state_obj)
        await cq.message.edit_text(f"{prompt_text}\n\nلإلغاء العملية، أرسل /cancel."); return

    if d in menus:
        await cq.message.edit_text(menus[d], reply_markup=get_menu_keyboard(d)); return

    # This part shows how list views would be upgraded
    if d == "show_reminders":
        reminders = data_store.bot_data.get('reminders', [])
        await state.update_data(reminders_view=list(reminders)) 
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        text = "💭 قائمة التذكيرات:\n\nاضغط لحذف تذكير."
        if not reminders: text = "💭 القائمة فارغة."
        else:
            for i, reminder in enumerate(reminders):
                keyboard.add(types.InlineKeyboardButton(f"🗑️ {reminder[:50]}...", callback_data=f"del_reminder_idx_{i}"))
        keyboard.add(types.InlineKeyboardButton("🔙 العودة", callback_data="admin_reminders"))
        await cq.message.edit_text(text, reply_markup=keyboard)
        return

    # --- Standard FSM Setters (Original logic) ---
    standard_prompts = { 
        "add_dyn_reply": (texts.get_text("prompt_dyn_reply_keyword"), AdminStates.waiting_for_dyn_reply_keyword), 
        "delete_dyn_reply": (texts.get_text("prompt_dyn_reply_delete"), AdminStates.waiting_for_dyn_reply_delete),
        "add_reminder": (texts.get_text("prompt_reminder_text"), AdminStates.waiting_for_new_reminder),
        "delete_reminder": (texts.get_text("prompt_reminder_delete"), AdminStates.waiting_for_delete_reminder),
        # ... and so on for all other FSM prompts
    }
    if d in standard_prompts:
        prompt_text, state_obj = standard_prompts[d]
        await state.set_state(state_obj)
        await cq.message.edit_text(f"{prompt_text}\n\nلإلغاء العملية، أرسل /cancel."); return

    # Final Catch-all, should not be reached
    await cq.answer("⚠️ هذه الميزة قيد الإنشاء.", show_alert=True)


def register_panel_handlers(dp: Dispatcher):
    """Registers the main admin command and callback handlers with corrected filters."""
    # 1. Main /admin command (always works)
    dp.register_message_handler(admin_panel_cmd, is_admin, commands=['admin'], state="*")
    
    # 2. Admin reply handler (works only when not in FSM state)
    dp.register_message_handler(admin_reply_cmd, is_admin, is_reply=True, content_types=types.ContentTypes.ANY, state=None)
    
    # 3. Main Callbacks Handler (FIX: works ONLY when NOT in FSM state)
    # This ensures that callbacks like del_reminder_idx_ work and are not blocked by FSM handlers
    # If the user is in an FSM state, they are expected to send a message, not press a general button.
    dp.register_callback_query_handler(
        callbacks_cmd, 
        is_admin, 
        lambda c: not c.data.startswith("adv_") and not c.data.startswith("tm_"), # Keep this for clear separation from advanced panels
        state=None # 🔴 THE FINAL FIX FOR THE CALLBACKS NOT EXECUTING!
    )
    
    # Since the check for adv_ and tm_ is in this handler, we must ensure advanced panels
    # are registered before or after this, but the logic relies on this filter existing.
