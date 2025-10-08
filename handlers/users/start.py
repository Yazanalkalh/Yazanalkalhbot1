from aiogram import types, Dispatcher
# ✅ تم الإصلاح: لم نعد نستخدم data_store هنا. نحن نتحدث مع قاعدة البيانات مباشرة
from utils import database, helpers
from keyboards.inline.user_keyboards import create_user_buttons
from config import ADMIN_CHAT_ID

async def start_cmd(message: types.Message):
    """Handler for the /start command for all users."""
    user = message.from_user
    
    # ✅ تم الإصلاح: استدعاء الدالة المخصصة لإضافة/تحديث المستخدم
    # هذه العملية الآن سريعة وآمنة وتحدث في جزء من الثانية
    database.add_user(
        user_id=user.id,
        full_name=user.full_name,
        username=user.username
    )
    
    # ✅ تم الإصلاح: جلب رسالة الترحيب مباشرة من قاعدة البيانات عبر دالة مخصصة
    welcome_template = database.get_setting("welcome_message", "👋 أهلًا وسهلًا بك, #name!")
    welcome_text = helpers.format_welcome_message(welcome_template, user)
    
    await message.reply(welcome_text, reply_markup=create_user_buttons())

async def admin_cmd_for_users(message: types.Message):
    """
    This handler catches the /admin command from non-admin users 
    and sends them a warning message.
    """
    warning_text = (
        "⚠️ <b>تنبيه خاص</b> 👑\n\n"
        "هذا الأمر مخصص للمدير فقط 🔒\n"
        "لا يمكنك استخدامه لضمان سلامة عمل البوت.\n\n"
        "<i>استخدم الأزرار المتاحة لك ✨</i>"
    )
    await message.reply(warning_text)

def register_start_handler(dp: Dispatcher):
    """Registers the handlers for /start and the /admin guard."""
    dp.register_message_handler(admin_cmd_for_users, lambda msg: msg.from_user.id != ADMIN_CHAT_ID, commands=['admin'], state="*")
    dp.register_message_handler(start_cmd, commands=['start'], state="*")
