from aiogram import types, Dispatcher

# استيراد المكونات اللازمة من الملفات الأخرى
from loader import bot
from config import ADMIN_CHAT_ID
from utils.helpers import *

# --- معالجات المستخدمين العاديين ---

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
                    (f"👋 أهلًا وسهلًا بك، {user_name}!\n"
                     "هذا البوت مخصص لملاحظاتك واستفساراتك.\n"
                     "تفضّل بطرح سؤالك وسيتم الرد عليك. ✨"))
    
    # استبدال {name} باسم المستخدم الفعلي
    final_text = welcome_text.replace("{name}", user_name)
    await message.reply(final_text, reply_markup=create_buttons(), parse_mode="Markdown")

async def handle_user_message(message: types.Message):
    """
    يعالج الرسائل النصية من المستخدمين بالمنطق الصحيح.
    1. يفحص الردود التلقائية.
    2. إذا لم يجد، يرسل للمشرف ثم يرد على المستخدم.
    """
    if is_banned(message.from_user.id): return

    user_id = message.from_user.id
    first_name = message.from_user.first_name or ""
    
    # التحقق من نظام منع الرسائل المزعجة
    spam_allowed, spam_status = check_spam_limit(user_id)
    if not spam_allowed:
        await message.reply(get_spam_warning_message(spam_status, first_name))
        return

    # -- المنطق الصحيح الذي طلبته --
    # الخطوة 1: فحص الردود التلقائية أولاً
    if message.text.strip() in AUTO_REPLIES:
        await message.reply(AUTO_REPLIES[message.text.strip()], reply_markup=create_buttons())
        return # يتوقف هنا إذا وجد رداً تلقائياً

    # الخطوة 2: إذا لم يكن هناك رد تلقائي، أرسل المحتوى للمشرف
    await handle_user_content(message, message.text)

    # الخطوة 3: أرسل رسالة تأكيد للمستخدم
    reply_text = bot_data.get("reply_message") or "✅ تم استلام رسالتك بنجاح، شكراً لتواصلك."
    await message.reply(reply_text, reply_markup=create_buttons())

async def handle_media_message(message: types.Message):
    """يعالج رسائل الوسائط (صور، فيديوهات، الخ) ويمنعها إذا لزم الأمر."""
    if is_banned(message.from_user.id): return

    # إذا كانت الوسائط غير مسموحة، امنعها
    if not bot_data.get("allow_media", False):
        reject_message = bot_data.get("media_reject_message", "❌ عذراً، يُسمح بالرسائل النصية فقط.")
        await message.reply(reject_message)
        bot_data["rejected_media_count"] = bot_data.get("rejected_media_count", 0) + 1
        save_data(bot_data)
        return
    
    # إذا كانت مسموحة، أرسلها للمشرف
    await handle_user_content(message, f"[{message.content_type}]")
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
        "from_developer": "تم تطوير هذا البوت بواسطة ✨ ابو سيف بن ذي يزن ✨"
    }
    
    if data in actions:
        await bot.send_message(user_id, actions[data], parse_mode="Markdown")

# --- تسجيل المعالجات ---

def register_user_handlers(dp: Dispatcher):
    """
    يسجل جميع المعالجات الخاصة بالمستخدم بالترتيب الصحيح.
    """
    dp.register_message_handler(send_welcome, commands=['start'], state="*")
    dp.register_callback_query_handler(process_user_callback, lambda q: q.from_user.id != ADMIN_CHAT_ID, state="*")
    
    # ** هذا هو التصحيح الأهم **
    # نسجل معالج الوسائط أولاً، ونحدد الأنواع بدقة (كل شيء ما عدا النص)
    media_types = [
        types.ContentType.PHOTO, types.ContentType.VIDEO, types.ContentType.DOCUMENT,
        types.ContentType.AUDIO, types.ContentType.VOICE, types.ContentType.VIDEO_NOTE,
        types.ContentType.STICKER, types.ContentType.ANIMATION
    ]
    dp.register_message_handler(handle_media_message, lambda m: m.from_user.id != ADMIN_CHAT_ID, content_types=media_types, state="*")

    # نسجل معالج النص أخيراً، ليعالج الرسائل النصية فقط
    dp.register_message_handler(handle_user_message, lambda m: m.from_user.id != ADMIN_CHAT_ID, content_types=types.ContentTypes.TEXT, state="*")


