from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text

from loader import bot
from config import ADMIN_CHAT_ID
from database import bot_data, save_data
from utils.helpers import (
    is_banned, create_user_buttons, get_hijri_date, get_live_time,
    get_daily_reminder, handle_user_content, AUTO_REPLIES, USERS_LIST
)

# --- معالج أمر /start ---
async def send_welcome(message: types.Message):
    """يرسل رسالة ترحيبية للمستخدم عند بدء المحادثة."""
    if is_banned(message.from_user.id):
        return

    user_id = message.from_user.id
    if user_id not in USERS_LIST:
        USERS_LIST.add(user_id)
        bot_data["users"] = list(USERS_LIST)
        save_data(bot_data)

    user_name = message.from_user.first_name or "عزيزي المستخدم"
    welcome_text = bot_data.get("welcome_message", "").format(name=user_name) or (
        f"👋 **أهلاً وسهلاً بك، {user_name}!**\n\n"
        "هذا البوت مخصص للتواصل مع فريق قناة التقويم الهجري.\n"
        "فضلاً، أرسل استفسارك أو ملاحظتك وسيتم الرد عليك في أقرب وقت.\n\n"
        "للوصول السريع، استخدم الأزرار أدناه. ✨"
    )
    await message.reply(welcome_text, reply_markup=create_user_buttons())

# --- معالج الرسائل النصية من المستخدم ---
async def handle_user_message(message: types.Message):
    """يعالج الرسائل النصية العادية من المستخدمين."""
    if is_banned(message.from_user.id):
        return

    user_message = message.text.strip()

    # 1. البحث عن رد تلقائي
    if user_message in AUTO_REPLIES:
        await message.reply(AUTO_REPLIES[user_message], reply_markup=create_user_buttons())
        return

    # 2. إذا لم يوجد رد، أرسل للمشرف
    await handle_user_content(message)

    # 3. أرسل رسالة تأكيد للمستخدم
    reply_text = bot_data.get("reply_message") or (
        "✅ **تم استلام رسالتك بنجاح!**\n\n"
        "شكراً لتواصلك معنا. سيقوم الفريق بمراجعة رسالتك والرد عليك في أقرب فرصة ممكنة. 🌙"
    )
    await message.reply(reply_text, reply_markup=create_user_buttons())

# --- معالج الوسائط من المستخدم ---
async def handle_media_message(message: types.Message):
    """يعالج جميع أنواع الوسائط (صور، فيديوهات، الخ) من المستخدمين."""
    if is_banned(message.from_user.id):
        return
    
    if not bot_data.get("allow_media", False):
        reject_message = bot_data.get("media_reject_message") or "❌ **عذراً، استقبال الوسائط معطل حالياً.**\nيُسمح بالرسائل النصية فقط."
        await message.reply(reject_message)
        return

    await handle_user_content(message)
    reply_text = bot_data.get("reply_message") or "✅ **تم استلام رسالتك بنجاح!**"
    await message.reply(reply_text, reply_markup=create_user_buttons())

# --- معالج أزرار المستخدم ---
async def process_user_callback(call: types.CallbackQuery):
    """يعالج الضغط على الأزرار من قبل المستخدم."""
    if is_banned(call.from_user.id):
        await call.answer("❌ أنت محظور من استخدام البوت.", show_alert=True)
        return

    await call.answer()
    data = call.data
    response_text = ""

    if data == "hijri_today":
        response_text = get_hijri_date()
    elif data == "live_time":
        response_text = get_live_time()
    elif data == "daily_reminder":
        response_text = get_daily_reminder()
    elif data == "from_developer":
        response_text = "👨‍💻 **تم تطوير هذا البوت بواسطة:**\n[فريق التقويم الهجري](https://t.me/HejriCalender)\n\nلخدمتكم والإجابة على استفساراتكم. ✨"
    
    if response_text:
        await call.message.answer(response_text, disable_web_page_preview=True, parse_mode="Markdown")

# --- دالة تسجيل المعالجات ---
def register_user_handlers(dp: Dispatcher):
    """تسجل جميع معالجات المستخدم في المرسل."""
    dp.register_message_handler(send_welcome, commands=['start'], state="*")
    dp.register_message_handler(handle_user_message, lambda msg: msg.from_user.id != ADMIN_CHAT_ID, content_types=types.ContentTypes.TEXT, state="*")
    dp.register_message_handler(handle_media_message, lambda msg: msg.from_user.id != ADMIN_CHAT_ID, content_types=types.ContentTypes.ANY, state="*")
    dp.register_callback_query_handler(process_user_callback, lambda call: call.from_user.id != ADMIN_CHAT_ID, state="*")
