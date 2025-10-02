from aiogram import types, Dispatcher
from loader import bot
from config import ADMIN_CHAT_ID
from utils.helpers import *

# --- معالجات المستخدمين ---

async def send_welcome(message: types.Message):
    """يرسل رسالة الترحيب عند بدء المحادثة."""
    if is_banned(message.from_user.id): return
    
    user_id = message.from_user.id
    if user_id not in USERS_LIST:
        USERS_LIST.add(user_id)
        bot_data["users"] = list(USERS_LIST)
        save_data(bot_data)

    user_name = message.from_user.first_name or "عزيزي المستخدم"
    welcome_text = (bot_data.get("welcome_message") or 
                    (f"👋 أهلًا وسهلًا بك يا {user_name}!\n\n"
                     "هذا البوت مخصص لملاحظاتك واستفساراتك.\n"
                     "تفضّل بطرح سؤالك وسيتم الرد عليك في أقرب وقت. ✨"))
    
    final_text = welcome_text.replace("{name}", user_name)
    await message.reply(final_text, reply_markup=create_buttons(), parse_mode="Markdown")

async def handle_user_message(message: types.Message):
    """يعالج الرسائل النصية من المستخدمين بالمنطق الصحيح."""
    if is_banned(message.from_user.id): return

    spam_allowed, spam_status = check_spam_limit(message.from_user.id)
    if not spam_allowed:
        await message.reply(get_spam_warning_message(spam_status, message.from_user.first_name))
        return

    user_text = message.text.strip()
    if user_text in AUTO_REPLIES:
        await message.reply(AUTO_REPLIES[user_text], reply_markup=create_buttons())
        return

    await handle_user_content(message)

    reply_text = bot_data.get("reply_message") or "✅ **تم استلام رسالتك بنجاح**\n\nشكراً لتواصلك معنا. سيتم مراجعتها والرد عليك قريباً."
    await message.reply(reply_text, reply_markup=create_buttons(), parse_mode="Markdown")

async def handle_media_message(message: types.Message):
    """يعالج رسائل الوسائط ويمنعها إذا لزم الأمر."""
    if is_banned(message.from_user.id): return

    if not bot_data.get("allow_media", False):
        reject_message = bot_data.get("media_reject_message", "❌ عذراً، يُسمح بالرسائل النصية فقط في الوقت الحالي.")
        await message.reply(reject_message)
        bot_data["rejected_media_count"] = bot_data.get("rejected_media_count", 0) + 1
        save_data(bot_data)
        return
    
    await handle_user_content(message)
    await message.reply("✅ تم استلام الوسائط بنجاح.", reply_markup=create_buttons())

async def process_user_callback(callback_query: types.CallbackQuery):
    """يعالج ضغطات الأزرار من المستخدمين."""
    if is_banned(callback_query.from_user.id):
        await bot.answer_callback_query(callback_query.id, "❌ أنت محظور من استخدام البوت!", show_alert=True)
        return
    
    await bot.answer_callback_query(callback_query.id)
    data = callback_query.data
    user_id = callback_query.from_user.id

    actions = {
        "hijri_today": get_hijri_date(),
        "live_time": get_live_time(),
        "daily_reminder": get_daily_reminder(),
        "from_developer": "تم تطوير هذا البوت بواسطة ✨ ابو سيف بن ذي يزن ✨\n[فريق التقويم الهجري](https://t.me/HejriCalender)"
    }
    
    if data in actions:
        await bot.send_message(user_id, actions[data], parse_mode="Markdown", disable_web_page_preview=True)

# --- تسجيل المعالجات ---
def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(send_welcome, commands=['start'], state="*")
    dp.register_callback_query_handler(process_user_callback, lambda q: q.from_user.id != ADMIN_CHAT_ID, state="*")
    
    media_types = [
        types.ContentType.PHOTO, types.ContentType.VIDEO, types.ContentType.DOCUMENT,
        types.ContentType.AUDIO, types.ContentType.VOICE, types.ContentType.VIDEO_NOTE,
        types.ContentType.STICKER, types.ContentType.ANIMATION, types.ContentType.CONTACT,
        types.ContentType.LOCATION
    ]
    dp.register_message_handler(handle_media_message, lambda m: m.from_user.id != ADMIN_CHAT_ID, content_types=media_types, state="*")
    dp.register_message_handler(handle_user_message, lambda m: m.from_user.id != ADMIN_CHAT_ID, content_types=types.ContentTypes.TEXT, state="*")


