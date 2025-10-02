from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

# Import necessary components from other files
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID, CHANNEL_ID
from utils.helpers import *
from utils.tasks import send_channel_message

# Handler for the /admin command to show the panel
async def admin_panel(message: types.Message):
    """Displays the main admin control panel."""
    await message.reply(
        "🔧 **لوحة التحكم الإدارية**\n\n"
        "مرحباً بك في لوحة التحكم الشاملة للبوت 🤖\n"
        "اختر الخيار المناسب من القائمة أدناه:",
        reply_markup=create_admin_panel(),
        parse_mode="Markdown"
    )

# Handler for admin replies to user messages
async def handle_admin_reply(message: types.Message):
    """Handles admin's text replies to forwarded user messages."""
    replied_to_message_id = message.reply_to_message.message_id
    admin_reply_text = message.text.strip()

    if replied_to_message_id in user_messages:
        user_info = user_messages[replied_to_message_id]
        user_id = user_info["user_id"]
        user_original_text = user_info["user_text"]

        if is_banned(user_id):
            await message.reply("❌ هذا المستخدم محظور!")
            return

        reply_message = f"رسالتك:\n{user_original_text}\n\n📩 رد من الإدارة:\n{admin_reply_text}"

        try:
            await bot.send_message(chat_id=user_id, text=reply_message)
            await message.reply("✅ تم إرسال الرد بنجاح للمستخدم")
        except Exception as e:
            await message.reply(f"❌ خطأ في إرسال الرد: {e}")
    else:
        await message.reply("❌ لم يتم العثور على الرسالة الأصلية. تأكد من أنك ترد على رسالة مستخدم.")

# Main handler for all admin panel button callbacks
async def process_admin_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Processes all button clicks from the admin panel."""
    await bot.answer_callback_query(callback_query.id) # Acknowledge the button press
    data = callback_query.data
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id

    # --- Main Menu Logic ---
    if data == "back_to_main":
        await state.finish()
        await bot.edit_message_text(
            "🔧 **لوحة التحكم الإدارية**\n\nاختر الخيار المناسب من القائمة أدناه:",
            chat_id=user_id, message_id=message_id, reply_markup=create_admin_panel(), parse_mode="Markdown"
        )
    elif data == "close_panel":
        await callback_query.message.delete()
        await bot.send_message(user_id, "✅ تم إغلاق لوحة التحكم")

    # --- Stats and Deployment ---
    elif data == "admin_stats":
        stats_text = (f"📊 **إحصائيات البوت**\n\n"
                      f"📝 الردود التلقائية: {len(AUTO_REPLIES)}\n"
                      f"💭 التذكيرات اليومية: {len(DAILY_REMINDERS)}\n"
                      f"📢 رسائل القناة: {len(CHANNEL_MESSAGES)}\n"
                      f"🚫 المستخدمين المحظورين: {len(BANNED_USERS)}\n"
                      f"👥 إجمالي المستخدمين: {len(USERS_LIST)}\n"
                      f"💬 المحادثات النشطة: {len(user_threads)}\n"
                      f"📨 الرسائل المحفوظة: {len(user_messages)}")
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main"))
        await bot.edit_message_text(stats_text, chat_id=user_id, message_id=message_id, reply_markup=keyboard, parse_mode="Markdown")
    
    # (The rest of the logic is now added here)
    elif data == "deploy_to_production":
        deployment_text = ("🚀 **نشر البوت للإنتاج (Render)**\n\n"
                         "✅ **الحالة الحالية:**\n"
                         "• البوت يعمل: ✅ نشط\n"
                         "• خادم الويب: ✅ يعمل لإبقاء البوت نشطًا\n"
                         "• قاعدة البيانات: ✅ سحابية (MongoDB)")
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_to_main"))
        await bot.edit_message_text(deployment_text, chat_id=user_id, message_id=message_id, reply_markup=keyboard, parse_mode="Markdown")

    # --- Sub-menus ---
    elif data == "admin_replies":
        keyboard = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("➕ إضافة رد", callback_data="add_reply"),
            InlineKeyboardButton("📝 عرض الردود", callback_data="show_replies"),
            InlineKeyboardButton("🗑️ حذف رد", callback_data="delete_reply_menu"),
            InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")
        )
        await bot.edit_message_text("📝 **إدارة الردود التلقائية**", chat_id=user_id, message_id=message_id, reply_markup=keyboard)

    # (Add all other menu handlers here similarly)
    
    # --- FSM Triggers ---
    elif data == "add_reply":
        await AdminStates.waiting_for_new_reply.set()
        await bot.edit_message_text("📝 **إضافة رد تلقائي جديد**\n\nأرسل الرد بالتنسيق التالي:\n`الكلمة المفتاحية|نص الرد`", chat_id=user_id, message_id=message_id, parse_mode="Markdown")
    
    # ... (all other elif conditions from your original file go here)

    # Example for another button:
    elif data == "admin_reminders":
        keyboard = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("➕ إضافة تذكير", callback_data="add_reminder"),
            InlineKeyboardButton("📝 عرض التذكيرات", callback_data="show_reminders"),
            InlineKeyboardButton("🗑️ حذف تذكير", callback_data="delete_reminder_menu"),
            InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")
        )
        await bot.edit_message_text("💭 **إدارة التذكيرات اليومية**", chat_id=user_id, message_id=message_id, reply_markup=keyboard)


# --- All FSM Handlers ---

async def process_new_reply(message: types.Message, state: FSMContext):
    """Handles the message after the 'add_reply' button is pressed."""
    try:
        trigger, response = map(str.strip, message.text.split('|', 1))
        AUTO_REPLIES[trigger] = response
        bot_data["auto_replies"] = AUTO_REPLIES
        save_data(bot_data)
        await message.reply(f"✅ تم إضافة الرد بنجاح!\n\n`{trigger}`", parse_mode="Markdown")
    except Exception as e:
        await message.reply(f"❌ خطأ في التنسيق. استخدم: `الكلمة|الرد`\n{e}")
    finally:
        await state.finish()
        await admin_panel(message) # Show main panel again

# (Add all other FSM state handlers from your original file here)
# e.g., process_new_reminder, process_ban_user, etc.


# --- Handler Registration ---

def register_admin_handlers(dp: Dispatcher):
    """Registers all admin-related handlers."""
    # Command to open the panel
    dp.register_message_handler(admin_panel, lambda m: m.from_user.id == ADMIN_CHAT_ID and m.text == "/admin", state="*")
    
    # Handler for text replies to user messages
    dp.register_message_handler(handle_admin_reply, lambda m: m.from_user.id == ADMIN_CHAT_ID and m.reply_to_message, content_types=types.ContentTypes.TEXT, state="*")

    # Single callback handler for all admin buttons
    dp.register_callback_query_handler(process_admin_callback, lambda q: q.from_user.id == ADMIN_CHAT_ID, state="*")

    # Register all FSM handlers
    dp.register_message_handler(process_new_reply, state=AdminStates.waiting_for_new_reply)
    # (Register all other state handlers here, for example:)
    # dp.register_message_handler(process_new_reminder, state=AdminStates.waiting_for_new_reminder)
    # dp.register_message_handler(process_ban_id, state=AdminStates.waiting_for_ban_id)


