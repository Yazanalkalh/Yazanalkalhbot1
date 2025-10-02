import asyncio
import datetime
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
from utils.tasks import send_channel_message
import data_store
from utils.helpers import create_admin_panel, forwarded_message_links # استيراد القاموس الجديد

async def admin_panel_cmd(message: types.Message):
    await message.reply("🔧 **لوحة التحكم الإدارية**", reply_markup=create_admin_panel())

async def admin_reply_cmd(message: types.Message):
    """
    يعالج رد المشرف على رسالة موجهة من مستخدم.
    هذه النسخة الجديدة تستخدم نظام الربط المضمون.
    """
    if not message.reply_to_message:
        return

    replied_to_msg_id = message.reply_to_message.message_id

    if replied_to_msg_id in forwarded_message_links:
        user_info = forwarded_message_links[replied_to_msg_id]
        user_id = user_info["user_id"]
        original_message_id = user_info["original_message_id"]

        try:
            await message.copy_to(
                chat_id=user_id,
                reply_to_message_id=original_message_id
            )
            await message.reply("✅ **تم إرسال ردك للمستخدم بنجاح.**")
            del forwarded_message_links[replied_to_msg_id] # تنظيف الذاكرة
        except Exception as e:
            await message.reply(f"❌ **فشل إرسال الرد.**\nقد يكون المستخدم قد حظر البوت.\nالخطأ: {e}")
    else:
        # هذا يعني أن المشرف يرد على رسالة عادية وليست رسالة موجهة من مستخدم
        pass # لا تفعل شيئاً لتجنب الإزعاج

# ... (بقية الكود تبقى كما هي تماماً)
# The rest of the file is provided for completeness and to avoid any issues.

async def callbacks_cmd(cq: types.CallbackQuery, state: FSMContext):
    await cq.answer()
    await state.finish()
    d = cq.data

    if d == "close_panel": await cq.message.delete()
    elif d == "back_to_main": await cq.message.edit_text("🔧 **لوحة التحكم الإدارية**", reply_markup=create_admin_panel())
    elif d == "admin_stats":
        s = f"📊 **إحصائيات:**\n- المستخدمون: {len(data_store.USERS_LIST)}\n- المحظورون: {len(data_store.BANNED_USERS)}\n- الردود: {len(data_store.AUTO_REPLIES)}"
        await cq.message.edit_text(s, reply_markup=back_kb("back_to_main"))
    elif d == "deploy_status":
        ut = datetime.datetime.now() - data_store.start_time
        s = f"🚀 **حالة النشر:**\n- الحالة: نشط\n- مدة التشغيل: {str(ut).split('.')[0]}"
        await cq.message.edit_text(s, reply_markup=back_kb("back_to_main"))
    elif d == "toggle_media":
        data_store.bot_data["allow_media"] = not data_store.bot_data.get("allow_media", False)
        data_store.save_all_data()
        status = "مسموح" if data_store.bot_data["allow_media"] else "ممنوع"
        await cq.answer(f"استقبال الوسائط الآن: {status}", show_alert=True)
        await cq.message.edit_text(f"🔒 **إدارة الوسائط**", reply_markup=get_kb("admin_media_settings"))
    elif d == "clear_temp_memory":
        c = len(data_store.user_message_count) + len(data_store.silenced_users)
        data_store.user_message_count.clear(); data_store.silenced_users.clear()
        await cq.answer(f"✅ تم مسح {c} سجل من ذاكرة الحماية.", show_alert=True)

    menus = {
        "admin_replies": "📝 **إدارة الردود**", "admin_reminders": "💭 **إدارة التذكيرات**",
        "admin_channel": "📢 **إدارة القناة**", "admin_ban": "🚫 **إدارة الحظر**",
        "admin_broadcast": "📤 **النشر الجماعي**", "admin_channel_settings": "⚙️ **إعدادات القناة**",
        "admin_messages_settings": "💬 **إعدادات الرسائل**", "admin_media_settings": "🔒 **إدارة الوسائط**",
        "admin_memory_management": "🧠 **إدارة الذاكرة**"
    }
    if d in menus:
        await cq.message.edit_text(menus[d], reply_markup=get_kb(d))

    lists = {
        "show_replies": ("📝 **الردود الحالية:**", "admin_replies", [f"🔹 `{k}`" for k in data_store.AUTO_REPLIES]),
        "show_reminders": ("💭 **التذكيرات الحالية:**", "admin_reminders", [f"{i+1}. {r[:40]}..." for i,r in enumerate(data_store.DAILY_REMINDERS)]),
        "show_channel_msgs": ("📢 **رسائل القناة:**", "admin_channel", [f"{i+1}. {m[:40]}..." for i,m in enumerate(data_store.CHANNEL_MESSAGES)]),
        "show_banned": ("🚫 **المحظورون:**", "admin_ban", [f"`{uid}`" for uid in data_store.BANNED_USERS])
    }
    if d in lists:
        title, back, items = lists[d]
        txt = title + "\n\n" + ("\n".join(items) if items else "لا يوجد شيء لعرضه.")
        await cq.message.edit_text(txt, reply_markup=back_kb(back))

    prompts = {
        "add_reply": ("📝 أرسل: `كلمة|رد`", AdminStates.waiting_for_new_reply),
        "delete_reply_menu": ("🗑️ أرسل الكلمة المفتاحية للحذف:", AdminStates.waiting_for_delete_reply),
        "add_reminder": ("💭 أرسل نص التذكير:", AdminStates.waiting_for_new_reminder),
        "delete_reminder_menu": ("🗑️ أرسل رقم التذكير للحذف:", AdminStates.waiting_for_delete_reminder),
        "add_channel_msg": ("➕ أرسل رسالة القناة:", AdminStates.waiting_for_new_channel_message),
        "delete_channel_msg_menu": ("🗑️ أرسل رقم الرسالة للحذف:", AdminStates.waiting_for_delete_channel_msg),
        "instant_channel_post": ("📤 أرسل رسالة للنشر الفوري:", AdminStates.waiting_for_instant_channel_post),
        "ban_user": ("🚫 أرسل ID المستخدم للحظر:", AdminStates.waiting_for_ban_id),
        "unban_user": ("✅ أرسل ID المستخدم لإلغاء الحظر:", AdminStates.waiting_for_unban_id),
        "send_broadcast": ("📤 أرسل رسالة جماعية:", AdminStates.waiting_for_broadcast_message),
        "set_channel_id": ("🆔 أرسل ID القناة:", AdminStates.waiting_for_channel_id),
        "set_schedule_time": ("⏰ أرسل الفترة بالساعات:", AdminStates.waiting_for_schedule_time),
        "set_welcome_msg": ("👋 أرسل رسالة الترحيب:", AdminStates.waiting_for_welcome_message),
        "set_reply_msg": ("💬 أرسل رسالة الرد:", AdminStates.waiting_for_reply_message),
        "set_media_reject_msg": ("✏️ أرسل رسالة الرفض:", AdminStates.waiting_for_media_reject_message),
        "clear_user_messages": ("🗑️ أرسل ID المستخدم للمسح:", AdminStates.waiting_for_clear_user_id),
    }
    if d in prompts:
        await state.set_state(prompts[d][1])
        await cq.message.edit_text(f"{prompts[d][0]}\n\nلإلغاء العملية، أرسل /cancel.")

def get_kb(menu):
    kb = InlineKeyboardMarkup(row_width=2)
    b_map = {
        "admin_replies": [("➕ إضافة", "add_reply"), ("📝 عرض", "show_replies"), ("🗑️ حذف", "delete_reply_menu")],
        "admin_reminders": [("➕ إضافة", "add_reminder"), ("📝 عرض", "show_reminders"), ("🗑️ حذف", "delete_reminder_menu")],
        "admin_channel": [("➕ إضافة", "add_channel_msg"), ("📝 عرض", "show_channel_msgs"), ("🗑️ حذف", "delete_channel_msg_menu"), ("📤 نشر فوري", "instant_channel_post")],
        "admin_ban": [("🚫 حظر", "ban_user"), ("✅ إلغاء حظر", "unban_user"), ("📋 عرض", "show_banned")],
        "admin_broadcast": [("📤 إرسال", "send_broadcast")],
        "admin_channel_settings": [("🆔 تعديل ID", "set_channel_id"), ("⏰ تعديل الفترة", "set_schedule_time")],
        "admin_messages_settings": [("👋 رسالة الترحيب", "set_welcome_msg"), ("💬 رسالة الرد", "set_reply_msg")],
        "admin_media_settings": [("🔓/🔒 تبديل الحالة", "toggle_media"), ("✏️ رسالة الرفض", "set_media_reject_msg")],
        "admin_memory_management": [("🗑️ مسح بيانات", "clear_user_messages"), ("🧹 مسح ذاكرة Spam", "clear_temp_memory")]
    }
    kb.add(*[InlineKeyboardButton(t, callback_data=c) for t,c in b_map.get(menu, [])])
    kb.add(InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="back_to_main"))
    return kb

def back_kb(cb): return InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 العودة", callback_data=cb))

async def cancel_cmd(m: types.Message, state: FSMContext):
    await state.finish()
    await m.reply("✅ تم إلغاء العملية.", reply_markup=create_admin_panel())

async def process_text(m: types.Message, s: FSMContext, key: str, is_list=False, success_msg=""):
    val = m.text.strip()
    if is_list:
        if key in data_store.bot_data and isinstance(data_store.bot_data[key], list):
            data_store.bot_data[key].append(val)
        else: # If key doesn't exist or is not a list, create it
            data_store.bot_data[key] = [val]
            if key == 'daily_reminders': data_store.DAILY_REMINDERS.append(val)
            if key == 'channel_messages': data_store.CHANNEL_MESSAGES.append(val)
    else:
        data_store.bot_data[key] = val
    data_store.save_all_data()
    await m.reply(success_msg.format(val=val), reply_markup=create_admin_panel())
    await s.finish()

async def new_reply(m: types.Message, s: FSMContext):
    try:
        k, v = map(str.strip, m.text.split('|', 1))
        data_store.AUTO_REPLIES[k] = v
        data_store.save_all_data()
        await m.reply(f"✅ **تم إضافة الرد:**\nعندما يقول: `{k}`\nسيرد: {v}", reply_markup=create_admin_panel())
    except: await m.reply("❌ **تنسيق خاطئ!**")
    await s.finish()

async def del_reply(m: types.Message, s: FSMContext):
    k = m.text.strip()
    if k in data_store.AUTO_REPLIES:
        del data_store.AUTO_REPLIES[k]
        data_store.save_all_data()
        await m.reply(f"✅ تم حذف الرد الخاص بـ `{k}`.", reply_markup=create_admin_panel())
    else: await m.reply(f"❌ لم يتم العثور على رد لـ `{k}`.")
    await s.finish()

async def del_by_idx(m: types.Message, s: FSMContext, lst: list, name: str):
    try:
        idx = int(m.text.strip()) - 1
        if 0 <= idx < len(lst):
            removed = lst.pop(idx)
            data_store.save_all_data()
            await m.reply(f"✅ تم حذف {name}:\n`{removed}`", reply_markup=create_admin_panel())
        else: await m.reply(f"❌ رقم غير صالح.")
    except: await m.reply("❌ الرجاء إرسال رقم.")
    await s.finish()

async def ban_user(m: types.Message, s: FSMContext):
    try:
        uid = int(m.text.strip())
        data_store.BANNED_USERS.add(uid)
        data_store.save_all_data()
        await m.reply(f"🚫 تم حظر المستخدم `{uid}`.", reply_markup=create_admin_panel())
    except: await m.reply("❌ ID غير صالح.")
    await s.finish()

async def unban_user(m: types.Message, s: FSMContext):
    try:
        uid = int(m.text.strip())
        if uid in data_store.BANNED_USERS:
            data_store.BANNED_USERS.remove(uid)
            data_store.save_all_data()
            await m.reply(f"✅ تم إلغاء حظر `{uid}`.", reply_markup=create_admin_panel())
        else: await m.reply("❌ المستخدم غير محظور.")
    except: await m.reply("❌ ID غير صالح.")
    await s.finish()

async def broadcast(m: types.Message, s: FSMContext):
    s_count, f_count = 0, 0
    for uid in data_store.USERS_LIST:
        try:
            await m.copy_to(uid); s_count += 1
            await asyncio.sleep(0.1)
        except: f_count += 1
    await m.reply(f"✅ **اكتمل الإرسال:**\n- نجح: {s_count}\n- فشل: {f_count}", reply_markup=create_admin_panel())
    await s.finish()

async def clear_user(m: types.Message, s: FSMContext):
    try:
        uid = int(m.text.strip())
        c=0
        if uid in data_store.user_message_count: del data_store.user_message_count[uid]; c+=1
        if uid in data_store.silenced_users: del data_store.silenced_users[uid]; c+=1
        await m.reply(f"✅ تم مسح {c} سجل حماية للمستخدم `{uid}`.", reply_markup=create_admin_panel())
    except: await m.reply("❌ ID غير صالح.")
    await s.finish()

async def set_schedule(m: types.Message, s: FSMContext):
    try:
        h = float(m.text.strip())
        data_store.bot_data["schedule_interval_seconds"] = int(h * 3600)
        data_store.save_all_data()
        await m.reply(f"✅ تم تحديث فترة النشر إلى كل {h} ساعة.", reply_markup=create_admin_panel())
    except: await m.reply("❌ رقم غير صالح.")
    await s.finish()

def register_admin_handlers(dp: Dispatcher):
    admin_id_filter = lambda m: m.from_user.id == ADMIN_CHAT_ID
    dp.register_message_handler(admin_panel_cmd, admin_id_filter, commands=['admin'], state="*")
    dp.register_message_handler(admin_reply_cmd, admin_id_filter, is_reply=True, content_types=types.ContentTypes.ANY, state="*")
    dp.register_callback_query_handler(callbacks_cmd, admin_id_filter, state="*")
    dp.register_message_handler(cancel_cmd, admin_id_filter, commands=['cancel'], state='*')

    dp.register_message_handler(new_reply, admin_id_filter, state=AdminStates.waiting_for_new_reply)
    dp.register_message_handler(del_reply, admin_id_filter, state=AdminStates.waiting_for_delete_reply)
    dp.register_message_handler(lambda m,s: process_text(m,s,"daily_reminders",True, "✅ **تم إضافة التذكير:** {val}"), admin_id_filter, state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(lambda m,s: del_by_idx(m,s,data_store.DAILY_REMINDERS, "التذكير"), admin_id_filter, state=AdminStates.waiting_for_delete_reminder)
    dp.register_message_handler(lambda m,s: process_text(m,s,"channel_messages",True, "✅ **تم إضافة رسالة القناة:** {val}"), admin_id_filter, state=AdminStates.waiting_for_new_channel_message)
    dp.register_message_handler(lambda m,s: del_by_idx(m,s,data_store.CHANNEL_MESSAGES, "الرسالة"), admin_id_filter, state=AdminStates.waiting_for_delete_channel_msg)
    dp.register_message_handler(lambda m,s: asyncio.ensure_future(send_channel_message(m.text)) and m.reply("✅ تم الإرسال للقناة.", reply_markup=create_admin_panel()) and s.finish(), admin_id_filter, state=AdminStates.waiting_for_instant_channel_post)
    dp.register_message_handler(ban_user, admin_id_filter, state=AdminStates.waiting_for_ban_id)
    dp.register_message_handler(unban_user, admin_id_filter, state=AdminStates.waiting_for_unban_id)
    dp.register_message_handler(broadcast, admin_id_filter, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_broadcast_message)
    dp.register_message_handler(lambda m,s: process_text(m,s,"channel_id",False, "✅ **تم تحديث ID القناة إلى:** {val}"), admin_id_filter, state=AdminStates.waiting_for_channel_id)
    dp.register_message_handler(set_schedule, admin_id_filter, state=AdminStates.waiting_for_schedule_time)
    dp.register_message_handler(lambda m,s: process_text(m,s,"welcome_message",False, "✅ **تم تحديث رسالة الترحيب.**"), admin_id_filter, state=AdminStates.waiting_for_welcome_message)
    dp.register_message_handler(lambda m,s: process_text(m,s,"reply_message",False, "✅ **تم تحديث رسالة الرد.**"), admin_id_filter, state=AdminStates.waiting_for_reply_message)
    dp.register_message_handler(lambda m,s: process_text(m,s,"media_reject_message",False, "✅ **تم تحديث رسالة الرفض.**"), admin_id_filter, state=AdminStates.waiting_for_media_reject_message)
    dp.register_message_handler(clear_user, admin_id_filter, state=AdminStates.waiting_for_clear_user_id)
