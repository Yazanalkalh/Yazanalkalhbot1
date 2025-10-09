import datetime
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
# ✅ تم الإصلاح: الآن يستورد ID المدير من المكان الصحيح
from config import ADMIN_CHAT_ID
from utils import database, texts
from states.admin_states import AdminStates
from keyboards.inline.admin_keyboards import create_admin_panel, get_menu_keyboard, back_kb

# ✅ تم الإصلاح: الفلتر الآن يستخدم المتغير الصحيح
def is_admin(message: types.Message):
    return message.from_user.id == ADMIN_CHAT_ID

async def admin_panel_cmd(m: types.Message, state: FSMContext):
    if await state.get_state() is not None:
        await state.finish()
    await m.reply(texts.get_text("admin_panel_title"), reply_markup=create_admin_panel())

async def admin_reply_cmd(m: types.Message, state: FSMContext):
    if not m.reply_to_message: return
    link = database.get_forwarded_link(m.reply_to_message.message_id)
    if link:
        try:
            await m.copy_to(link["user_id"], reply_to_message_id=link["original_message_id"])
            await m.reply(texts.get_text("admin_reply_sent"))
        except Exception as e:
            await m.reply(texts.get_text("admin_reply_fail", e=e))

async def callbacks_cmd(cq: types.CallbackQuery, state: FSMContext):
    await cq.answer()
    d = cq.data
    
    if d == "close_panel": await cq.message.delete(); return
    if d == "back_to_main": 
        await cq.message.edit_text(texts.get_text("admin_panel_title"), reply_markup=create_admin_panel())
        return
    
    # ... (بقية منطق الأزرار هنا سليم)
    # This part handles deletions and other interactions
    if d == "admin_stats":
        stats = database.get_db_stats()
        uptime = datetime.datetime.now() - database.start_time
        stats_text = (f"📊 **إحصائيات البوت:**\n\n"
                      f"👥 المستخدمون: {stats.get('users_count', 0)}\n"
                      f"⏱️ وقت التشغيل: {str(uptime).split('.')[0]}")
        await cq.message.edit_text(stats_text, reply_markup=back_kb()); return
        
    # Other handlers for setting states
    standard_prompts = { 
        "add_dyn_reply": (texts.get_text("prompt_dyn_reply_keyword"), AdminStates.waiting_for_dyn_reply_keyword),
        "add_reminder": (texts.get_text("prompt_reminder_text"), AdminStates.waiting_for_new_reminder),
    }
    if d in standard_prompts:
        prompt_text, state_obj = standard_prompts[d]
        await state.set_state(state_obj)
        await cq.message.edit_text(f"{prompt_text}\n\nلإلغاء العملية، أرسل /cancel."); return

def register_panel_handlers(dp: Dispatcher):
    dp.register_message_handler(admin_panel_cmd, is_admin, commands=['admin'], state="*")
    dp.register_message_handler(admin_reply_cmd, is_admin, is_reply=True, content_types=types.ContentTypes.ANY, state=None)
    dp.register_callback_query_handler(callbacks_cmd, is_admin, lambda c: not c.data.startswith("adv_") and not c.data.startswith("tm_"), state=None)
