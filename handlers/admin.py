from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID, CHANNEL_ID
from utils.helpers import *
from utils.tasks import send_channel_message

async def admin_panel(message: types.Message):
    await message.reply("🔧 **لوحة التحكم الإدارية**\n\nاختر الخيار المناسب من القائمة أدناه:", reply_markup=create_admin_panel(), parse_mode="Markdown")

async def handle_admin_reply(message: types.Message):
    replied_to_id = message.reply_to_message.message_id
    if replied_to_id in user_messages:
        user_info = user_messages[replied_to_id]
        user_id = user_info["user_id"]
        if is_banned(user_id):
            await message.reply("❌ هذا المستخدم محظور!")
            return
        reply_text = f"رسالتك:\n{user_info['user_text']}\n\n📩 رد من الإدارة:\n{message.text}"
        try:
            await bot.send_message(user_id, reply_text)
            await message.reply("✅ تم إرسال الرد بنجاح للمستخدم")
        except Exception as e:
            await message.reply(f"❌ خطأ في إرسال الرد: {e}")
    else:
        await message.reply("❌ لم يتم العثور على الرسالة الأصلية.")

# This single function will handle all admin callbacks to keep it clean.
async def process_admin_callback(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    data = query.data
    # (Here we will paste the entire logic from the original process_admin_callback function)
    if data == "admin_stats":
        stats_text = (f"📊 **إحصائيات البوت**\n\n"
                      f"📝 الردود: {len(AUTO_REPLIES)}\n"
                      f"💭 التذكيرات: {len(DAILY_REMINDERS)}\n"
                      f"📢 رسائل القناة: {len(CHANNEL_MESSAGES)}\n"
                      f"🚫 المحظورين: {len(BANNED_USERS)}\n"
                      f"👥 المستخدمين: {len(USERS_LIST)}\n"
                      f"💬 المحادثات: {len(user_threads)}")
        await bot.edit_message_text(stats_text, query.from_user.id, query.message.message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")), parse_mode="Markdown")
    
    # --- Other admin callbacks ---
    # (The full logic from the original file should be here)
    elif data == "back_to_main":
        await state.finish()
        await bot.edit_message_text("🔧 **لوحة التحكم الإدارية**", query.from_user.id, query.message.message_id, reply_markup=create_admin_panel(), parse_mode="Markdown")
    elif data == "close_panel":
        await query.message.delete()
        await bot.send_message(query.from_user.id, "✅ تم إغلاق لوحة التحكم")

# And all other `process_...` FSM handlers go here...
async def process_new_reply(message: types.Message, state: FSMContext):
    try:
        trigger, response = map(str.strip, message.text.split('|', 1))
        AUTO_REPLIES[trigger] = response
        bot_data["auto_replies"] = AUTO_REPLIES
        save_data(bot_data)
        await message.reply(f"✅ تم إضافة الرد بنجاح!\n`{trigger}` -> `{response}`", parse_mode="Markdown")
    except Exception as e:
        await message.reply(f"❌ خطأ: {e}. استخدم الصيغة: `الكلمة|الرد`")
    await state.finish()
# (All other FSM handlers like process_new_reminder, process_ban_user etc. go here)

def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(admin_panel, lambda m: m.from_user.id == ADMIN_CHAT_ID and m.text == "/admin", state="*")
    dp.register_message_handler(handle_admin_reply, lambda m: m.from_user.id == ADMIN_CHAT_ID and m.reply_to_message, content_types=types.ContentTypes.TEXT, state="*")
    dp.register_callback_query_handler(process_admin_callback, lambda q: q.from_user.id == ADMIN_CHAT_ID, state="*")
    # Register all FSM handlers
    dp.register_message_handler(process_new_reply, state=AdminStates.waiting_for_new_reply)
    # (Register all other FSM handlers here...)


 
