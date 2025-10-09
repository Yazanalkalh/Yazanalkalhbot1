from aiogram import types, Dispatcher
from config import ADMIN_CHAT_ID
from loader import bot
# نستورد الدالة الصحيحة من قاعدة البيانات
from utils.database import add_pending_channel

# هذا هو الملف الكامل والصحيح
# وظيفته هي اكتشاف انضمام البوت إلى قناة جديدة وإبلاغ المدير

async def on_bot_join_chat(message: types.Message):
    """
    هذا المعالج يعمل عندما تتم إضافة البوت إلى مجموعة أو قناة جديدة.
    يقوم بإضافة المحادثة إلى قائمة الانتظار ويبلغ المدير.
    """
    # هذا التحقق يضمن أن الحدث يتعلق بانضمام البوت نفسه
    for member in message.new_chat_members:
        if member.id == bot.id:
            chat_id = message.chat.id
            chat_title = message.chat.title
            
            # الإضافة إلى قاعدة البيانات لموافقة المدير
            add_pending_channel(chat_id, chat_title)
            
            # إبلاغ المدير
            text = (
                f"⏳ **طلب انضمام جديد**\n\n"
                f"تمت إضافة البوت إلى قناة/مجموعة جديدة وهي تنتظر موافقتك:\n\n"
                f"**الاسم:** {chat_title}\n"
                f"**ID:** `{chat_id}`\n\n"
                f"اذهب إلى **لوحة التحكم المتقدمة (`/hijri`)** -> **إدارة القنوات** للموافقة أو الرفض."
            )
            await bot.send_message(ADMIN_CHAT_ID, text)
            break # لا حاجة للتحقق من بقية الأعضاء الجدد

# 🔴 هذا هو "الموظف المفقود" الذي كنا نبحث عنه
# هذه الدالة هي التي يتم استيرادها في ملف __init__.py
def register_chat_admin_handler(dp: Dispatcher):
    """يسجل المعالج الخاص بتغييرات عضوية المحادثة."""
    # هذا المعالج يبحث تحديدًا عن الرسائل من نوع "أعضاء جدد في المحادثة"
    dp.register_message_handler(
        on_bot_join_chat,
        content_types=types.ContentTypes.NEW_CHAT_MEMBERS
    )
