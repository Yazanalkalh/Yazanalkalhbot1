import asyncio
import datetime
import pytz
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
import data_store
from keyboards.inline import create_admin_panel, get_menu_keyboard, back_kb

# --- معالج أمر /admin ---
async def admin_panel_cmd(message: types.Message):
    await message.reply("🔧 **لوحة التحكم الإدارية**\n\nأهلاً بك. اختر الإجراء المطلوب:", reply_markup=create_admin_panel())

# --- معالج رد المشرف على رسائل المستخدمين ---
async def admin_reply_cmd(message: types.Message):
    if not message.reply_to_message: return
    
    replied_to_msg_id = message.reply_to_message.message_id
    if replied_to_msg_id in data_store.forwarded_message_links:
        user_info = data_store.forwarded_message_links[replied_to_msg_id]
        try:
            await message.copy_to(
                chat_id=user_info["user_id"],
                reply_to_message_id=user_info["original_message_id"]
            )
            await message.reply("✅ **تم إرسال ردك للمستخدم بنجاح.**")
            # حذف الرابط بعد الرد لمنع الردود المتعددة على نفس الرسالة
            del data_store.forwarded_message_links[replied_to_msg_id]
        except Exception as e:
            await message.reply(f"❌ **فشل إرسال الرد.**\nالخطأ: {e}")

# --- المعالج الرئيسي لأزرار لوحة التحكم ---
async def callbacks_cmd(cq: types.CallbackQuery, state: FSMContext):
    await cq.answer()
    await state.finish()
    d = cq.data

    # --- الأزرار الفورية ---
    if d == "close_panel":
        await cq.message.delete()
        return
    elif d == "back_to_main":
        await cq.message.edit_text("🔧 **لوحة التحكم الإدارية**", reply_markup=create_admin_panel())
        return
    elif d == "admin_stats":
        stats = (
            f"📊 **إحصائيات البوت الحالية:**\n\n"
            f"👥 **إجمالي المستخدمين:** {len(data_store.bot_data['users'])}\n"
            f"🚫 **المستخدمون المحظورون:** {len(data_store.bot_data['banned_users'])}\n"
            f"💬 **الردود الديناميكية:** {len(data_store.bot_data['dynamic_replies'])}\n"
            f"💡 **التذكيرات:** {len(data_store.bot_data['reminders'])}"
        )
        await cq.message.edit_text(stats, reply_markup=back_kb("back_to_main"))
        return
    elif d == "deploy_status":
        uptime = datetime.datetime.now() - data_store.start_time
        status = (
            f"🚀 **حالة النشر (Deploy):**\n\n"
            f"✅ **الحالة:** نشط ومستقر\n"
            f"⏰ **مدة التشغيل:** {str(uptime).split('.')[0]}"
        )
        await cq.message.edit_text(status, reply_markup=back_kb("back_to_main"))
        return
    elif d == "toggle_media":
        current_status = data_store.bot_data['bot_config'].get('allow_media', False)
        data_store.bot_data['bot_config']['allow_media'] = not current_status
        data_store.save_data()
        status_text = "مسموح الآن" if not current_status else "ممنوع الآن"
        await cq.answer(f"تم تغيير حالة استقبال الوسائط إلى: {status_text}", show_alert=True)
        await cq.message.edit_text("🔒 **إدارة الوسائط**", reply_markup=get_menu_keyboard("admin_media_settings"))
        return
    elif d == "clear_spam_cache":
        count = len(data_store.user_message_count) + len(data_store.silenced_users)
        data_store.user_message_count.clear()
        data_store.silenced_users.clear()
        await cq.answer(f"✅ تم بنجاح مسح {count} سجل من ذاكرة الحماية المؤقتة.", show_alert=True)
        return

    # --- القوائم الفرعية ---
    menus = {
        "admin_dyn_replies": "📝 **إدارة الردود الديناميكية**", "admin_reminders": "💭 **إدارة التذكيرات**",
        "admin_channel": "📢 **إدارة القناة**", "admin_ban": "🚫 **إدارة الحظر**",
        "admin_customize_ui": "🎨 **تخصيص واجهة البوت**", "admin_media_settings": "🔒 **إدارة الوسائط**",
        "admin_memory_management": "🧠 **إدارة الذاكرة**"
    }
    if d in menus:
        await cq.message.edit_text(f"{menus[d]}\n\nاختر الإجراء المطلوب:", reply_markup=get_menu_keyboard(d))
        return

    # --- قوائم العرض ---
    lists = {
        "show_dyn_replies": ("📝 **الردود المبرمجة حالياً:**", "admin_dyn_replies", [f"🔹 `{k}`" for k in data_store.bot_data['dynamic_replies']]),
        "show_reminders": ("💭 **التذكيرات الحالية:**", "admin_reminders", [f"{i+1}. {r[:40]}..." for i, r in enumerate(data_store.bot_data['reminders'])]),
        "show_channel_msgs": ("📢 **رسائل القناة التلقائية:**", "admin_channel", [f"{i+1}. {m[:40]}..." for i, m in enumerate(data_store.bot_data['channel_messages'])]),
        "show_banned": ("🚫 **المحظورون حالياً:**", "admin_ban", [f"`{uid}`" for uid in data_store.bot_data['banned_users']])
    }
    if d in lists:
        title, back_callback, items = lists[d]
        text = title + "\n\n" + ("\n".join(items) if items else "لا يوجد شيء لعرضه حالياً.")
        await cq.message.edit_text(text, reply_markup=back_kb(back_callback))
        return

    # --- طلبات الإدخال (FSM) ---
    prompts = {
        "add_dyn_reply": ("📝 **برمجة رد جديد:**\n\nأولاً، أرسل **الكلمة المفتاحية** التي سيكتبها المستخدم.", AdminStates.waiting_for_dyn_reply_keyword),
        "delete_dyn_reply": ("🗑️ **حذف رد مبرمج:**\n\nأرسل الكلمة المفتاحية للرد الذي تريد حذفه.", AdminStates.waiting_for_dyn_reply_delete),
        "add_reminder": ("💭 **إضافة تذكير:**\n\nأرسل نص التذكير الجديد.", AdminStates.waiting_for_new_reminder),
        "delete_reminder": ("🗑️ **حذف تذكير:**\n\nأرسل رقم التذكير الذي تريد حذفه (بدءاً من 1).", AdminStates.waiting_for_delete_reminder),
        "add_channel_msg": ("➕ **إضافة رسالة تلقائية للقناة:**\n\nأرسل نص الرسالة.", AdminStates.waiting_for_new_channel_msg),
        "delete_channel_msg": ("🗑️ **حذف رسالة تلقائية:**\n\nأرسل رقم الرسالة للحذف.", AdminStates.waiting_for_delete_channel_msg),
        "instant_channel_post": ("📤 **نشر فوري:**\n\nأرسل الرسالة التي تريد نشرها الآن في القناة.", AdminStates.waiting_for_instant_channel_post),
        "schedule_post": ("⏰ **جدولة رسالة محددة:**\n\nأولاً، أرسل **نص الرسالة** التي تريد جدولتها.", AdminStates.waiting_for_scheduled_post_text),
        "ban_user": ("🚫 **حظر مستخدم:**\n\nأرسل ID المستخدم الرقمي.", AdminStates.waiting_for_ban_id),
        "unban_user": ("✅ **إلغاء حظر:**\n\nأرسل ID المستخدم الرقمي.", AdminStates.waiting_for_unban_id),
        "edit_date_button": ("✏️ **تعديل زر التاريخ:**\n\nأرسل الاسم الجديد للزر.", AdminStates.waiting_for_date_button_label),
        "edit_time_button": ("✏️ **تعديل زر الساعة:**\n\nأرسل الاسم الجديد للزر.", AdminStates.waiting_for_time_button_label),
        "edit_reminder_button": ("✏️ **تعديل زر التذكير:**\n\nأرسل الاسم الجديد للزر.", AdminStates.waiting_for_reminder_button_label),
        "edit_welcome_msg": ("👋 **تعديل رسالة الترحيب:**\n\nأرسل النص الجديد. يمكنك استخدام الهاشتاقات.", AdminStates.waiting_for_welcome_message),
        "edit_reply_msg": ("💬 **تعديل رسالة الرد:**\n\nأرسل نص الرد التلقائي الجديد.", AdminStates.waiting_for_reply_message),
        "edit_media_reject_msg": ("✏️ **تعديل رسالة الرفض:**\n\nأرسل نص رسالة رفض الوسائط الجديد.", AdminStates.waiting_for_media_reject_message),
        "clear_user_data": ("🗑️ **مسح بيانات مستخدم:**\n\nأرسل ID المستخدم لمسح بيانات الحماية المؤقتة الخاصة به.", AdminStates.waiting_for_clear_user_id),
    }
    if d in prompts:
        prompt_text, state_to_set = prompts[d]
        await state.set_state(state_to_set)
        await cq.message.edit_text(f"{prompt_text}\n\nلإلغاء العملية، أرسل /cancel.")
        return

# --- معالجات حالات FSM ---

async def cancel_cmd(m: types.Message, state: FSMContext):
    """إلغاء أي عملية جارية."""
    await state.finish()
    await m.reply("✅ تم إلغاء العملية بنجاح.", reply_markup=create_admin_panel())

# -- برمجة الردود --
async def dyn_reply_keyword(m: types.Message, state: FSMContext):
    await state.update_data(keyword=m.text.strip())
    await m.reply("👍 **ممتاز!**\n\nالآن أرسل **المحتوى** الذي سيرد به البوت عندما يكتب المستخدم هذه الكلمة.")
    await AdminStates.next()

async def dyn_reply_content(m: types.Message, state: FSMContext):
    data = await state.get_data()
    keyword = data['keyword']
    content = m.text.strip()
    data_store.bot_data['dynamic_replies'][keyword] = content
    data_store.save_data()
    await m.reply(f"✅ **تمت برمجة الرد بنجاح!**\n\n**الكلمة المفتاحية:** `{keyword}`\n**محتوى الرد:** {content}", reply_markup=create_admin_panel())
    await state.finish()

async def dyn_reply_delete(m: types.Message, state: FSMContext):
    keyword = m.text.strip()
    if keyword in data_store.bot_data['dynamic_replies']:
        del data_store.bot_data['dynamic_replies'][keyword]
        data_store.save_data()
        await m.reply(f"✅ تم حذف الرد المبرمج الخاص بالكلمة: `{keyword}`", reply_markup=create_admin_panel())
    else:
        await m.reply(f"❌ لم يتم العثور على رد مبرمج لهذه الكلمة.", reply_markup=create_admin_panel())
    await state.finish()

# -- معالجات عامة --
async def process_text_input(m: types.Message, s: FSMContext, data_key: list, success_msg: str, is_list=False):
    """دالة عامة لمعالجة المدخلات النصية وحفظها."""
    value = m.text.strip()
    target_dict = data_store.bot_data
    for key in data_key[:-1]:
        target_dict = target_dict.setdefault(key, {})
    
    if is_list:
        target_dict.setdefault(data_key[-1], []).append(value)
    else:
        target_dict[data_key[-1]] = value
    
    data_store.save_data()
    await m.reply(success_msg.format(value=value), reply_markup=create_admin_panel())
    await s.finish()

async def process_delete_by_index(m: types.Message, s: FSMContext, data_key: list, item_name: str):
    """دالة عامة للحذف من قائمة بالرقم."""
    try:
        idx = int(m.text.strip()) - 1
        target_list = data_store.bot_data
        for key in data_key:
            target_list = target_list[key]

        if 0 <= idx < len(target_list):
            removed = target_list.pop(idx)
            data_store.save_data()
            await m.reply(f"✅ تم حذف {item_name}:\n`{removed}`", reply_markup=create_admin_panel())
        else:
            await m.reply(f"❌ رقم غير صالح. الرجاء إدخال رقم بين 1 و {len(target_list)}.")
    except (ValueError, IndexError):
        await m.reply("❌ الرجاء إرسال رقم صحيح وموجود في القائمة.")
    await s.finish()

# -- جدولة متقدمة --
async def scheduled_post_text(m: types.Message, state: FSMContext):
    await state.update_data(post_text=m.text.strip())
    await m.reply("👍 **ممتاز!**\n\nالآن أرسل **وقت وتاريخ الإرسال** بالتنسيق التالي (مثال):\n`2025-12-31 23:59`\n\n**ملاحظة:** التوقيت العالمي المنسق (UTC).")
    await AdminStates.next()

async def scheduled_post_datetime(m: types.Message, state: FSMContext):
    try:
        dt_str = m.text.strip()
        send_at = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        send_at_utc = pytz.utc.localize(send_at)
        
        data = await state.get_data()
        post_text = data['post_text']
        
        channel_id = data_store.bot_data['bot_config'].get('channel_id')
        if not channel_id:
            await m.reply("❌ **خطأ:** يجب تحديد ID القناة أولاً من `إدارة القناة` -> `تعديل ID القناة`.", reply_markup=create_admin_panel())
            await state.finish()
            return
            
        new_post = {
            "text": post_text,
            "channel_id": channel_id,
            "send_at_iso": send_at_utc.isoformat()
        }
        data_store.bot_data.setdefault("scheduled_posts", []).append(new_post)
        data_store.save_data()
        
        await m.reply(f"✅ **تمت جدولة الرسالة بنجاح!**\n\n**سيتم إرسالها إلى:** `{channel_id}`\n**في تاريخ:** `{dt_str} (UTC)`", reply_markup=create_admin_panel())
    except ValueError:
        await m.reply("❌ **تنسيق التاريخ خاطئ!**\nالرجاء استخدام التنسيق: `YYYY-MM-DD HH:MM`\nمثال: `2025-12-31 23:59`")
    await state.finish()

# -- حظر وإدارة --
async def ban_unban_user(m: types.Message, s: FSMContext, ban: bool):
    try:
        user_id = int(m.text.strip())
        if ban:
            data_store.bot_data['banned_users'].append(user_id)
            await m.reply(f"🚫 تم حظر المستخدم `{user_id}` بنجاح.", reply_markup=create_admin_panel())
        else:
            if user_id in data_store.bot_data['banned_users']:
                data_store.bot_data['banned_users'].remove(user_id)
                await m.reply(f"✅ تم إلغاء حظر `{user_id}`.", reply_markup=create_admin_panel())
            else:
                await m.reply(f"ℹ️ المستخدم `{user_id}` غير محظور أصلاً.")
        data_store.save_data()
    except ValueError:
        await m.reply("❌ الرجاء إرسال ID رقمي صحيح.")
    await s.finish()

async def broadcast_msg(m: types.Message, s: FSMContext):
    success, fail = 0, 0
    for user_id in data_store.bot_data['users']:
        try:
            await m.copy_to(user_id)
            success += 1
            await asyncio.sleep(0.1)
        except:
            fail += 1
    await m.reply(f"✅ **اكتمل الإرسال الجماعي:**\n\n- **نجح:** {success}\n- **فشل:** {fail}", reply_markup=create_admin_panel())
    await s.finish()

async def clear_user(m: types.Message, s: FSMContext):
    try:
        uid = int(m.text.strip()); c = 0
        if uid in data_store.user_message_count: del data_store.user_message_count[uid]; c += 1
        if uid in data_store.silenced_users: del data_store.silenced_users[uid]; c += 1
        await m.reply(f"✅ تم مسح {c} سجل حماية للمستخدم `{uid}`.", reply_markup=create_admin_panel())
    except ValueError:
        await m.reply("❌ الرجاء إرسال ID رقمي صحيح.")
    await s.finish()

# --- تخصيص الواجهة ---
async def set_timezone(m: types.Message, state: FSMContext):
    try:
        tz = m.text.strip()
        pytz.timezone(tz) # التحقق من صحة المنطقة الزمنية
        data_store.bot_data['ui_config']['timezone'] = tz
        data_store.save_data()
        await m.reply(f"✅ تم تحديث المنطقة الزمنية إلى: `{tz}`", reply_markup=create_admin_panel())
    except pytz.UnknownTimeZoneError:
        await m.reply("❌ **منطقة زمنية غير صالحة!**\nمثال للمناطق الصحيحة: `Asia/Aden`, `Asia/Riyadh`, `Africa/Cairo`")
    await state.finish()

# --- دالة تسجيل المعالجات ---
def register_admin_handlers(dp: Dispatcher):
    f = lambda m: m.from_user.id == ADMIN_CHAT_ID
    
    # المعالجات الأساسية
    dp.register_message_handler(admin_panel_cmd, f, commands=['admin'], state="*")
    dp.register_message_handler(admin_reply_cmd, f, is_reply=True, content_types=types.ContentTypes.ANY, state="*")
    dp.register_callback_query_handler(callbacks_cmd, f, state="*")
    dp.register_message_handler(cancel_cmd, f, commands=['cancel'], state='*')

    # معالجات حالات FSM
    # الردود الديناميكية
    dp.register_message_handler(dyn_reply_keyword, f, state=AdminStates.waiting_for_dyn_reply_keyword)
    dp.register_message_handler(dyn_reply_content, f, state=AdminStates.waiting_for_dyn_reply_content)
    dp.register_message_handler(dyn_reply_delete, f, state=AdminStates.waiting_for_dyn_reply_delete)
    
    # التذكيرات
    dp.register_message_handler(lambda m,s: process_text_input(m, s, ['reminders'], "✅ **تم إضافة التذكير:** {value}", is_list=True), f, state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(lambda m,s: process_delete_by_index(m, s, ['reminders'], "التذكير"), f, state=AdminStates.waiting_for_delete_reminder)
    
    # القناة
    dp.register_message_handler(lambda m,s: process_text_input(m, s, ['channel_messages'], "✅ **تم إضافة رسالة القناة:** {value}", is_list=True), f, state=AdminStates.waiting_for_new_channel_msg)
    dp.register_message_handler(lambda m,s: process_delete_by_index(m, s, ['channel_messages'], "الرسالة"), f, state=AdminStates.waiting_for_delete_channel_msg)
    dp.register_message_handler(lambda m,s: asyncio.ensure_future(send_channel_message(m.text.strip())) and m.reply("✅ تم الإرسال للقناة.", reply_markup=create_admin_panel()) and s.finish(), f, state=AdminStates.waiting_for_instant_channel_post)
    dp.register_message_handler(scheduled_post_text, f, state=AdminStates.waiting_for_scheduled_post_text)
    dp.register_message_handler(scheduled_post_datetime, f, state=AdminStates.waiting_for_scheduled_post_datetime)

    # الحظر
    dp.register_message_handler(lambda m,s: ban_unban_user(m, s, ban=True), f, state=AdminStates.waiting_for_ban_id)
    dp.register_message_handler(lambda m,s: ban_unban_user(m, s, ban=False), f, state=AdminStates.waiting_for_unban_id)
    
    # البث
    dp.register_message_handler(broadcast_msg, f, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_broadcast_message)
    
    # تخصيص الواجهة
    dp.register_message_handler(lambda m,s: process_text_input(m, s, ['ui_config', 'date_button_label'], "✅ **تم تحديث اسم زر التاريخ إلى:** {value}"), f, state=AdminStates.waiting_for_date_button_label)
    dp.register_message_handler(lambda m,s: process_text_input(m, s, ['ui_config', 'time_button_label'], "✅ **تم تحديث اسم زر الساعة إلى:** {value}"), f, state=AdminStates.waiting_for_time_button_label)
    dp.register_message_handler(lambda m,s: process_text_input(m, s, ['ui_config', 'reminder_button_label'], "✅ **تم تحديث اسم زر التذكير إلى:** {value}"), f, state=AdminStates.waiting_for_reminder_button_label)
    dp.register_message_handler(set_timezone, f, state=AdminStates.waiting_for_timezone)
    dp.register_message_handler(lambda m,s: process_text_input(m, s, ['bot_config', 'welcome_message'], "✅ **تم تحديث رسالة الترحيب.**"), f, state=AdminStates.waiting_for_welcome_message)
    dp.register_message_handler(lambda m,s: process_text_input(m, s, ['bot_config', 'reply_message'], "✅ **تم تحديث رسالة الرد.**"), f, state=AdminStates.waiting_for_reply_message)
    dp.register_message_handler(lambda m,s: process_text_input(m, s, ['bot_config', 'media_reject_message'], "✅ **تم تحديث رسالة الرفض.**"), f, state=AdminStates.waiting_for_media_reject_message)
    
    # الذاكرة
    dp.register_message_handler(clear_user, f, state=AdminStates.waiting_for_clear_user_id)


