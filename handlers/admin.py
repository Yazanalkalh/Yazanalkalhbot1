import asyncio
import datetime
import pytz
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
import data_store
from keyboards.inline import create_admin_panel, get_menu_keyboard, back_kb, add_another_kb
from utils.helpers import process_klisha

# --- Main Admin Command Handlers ---
async def admin_panel_cmd(message: types.Message):
    await message.reply("🔧 **لوحة التحكم الإدارية**\n\nأهلاً بك. اختر الإجراء المطلوب:", reply_markup=create_admin_panel())

async def admin_reply_cmd(message: types.Message):
    if not message.reply_to_message: return
    replied_to_msg_id = message.reply_to_message.message_id
    if replied_to_msg_id in data_store.forwarded_message_links:
        user_info = data_store.forwarded_message_links[replied_to_msg_id]
        try:
            await message.copy_to(chat_id=user_info["user_id"], reply_to_message_id=user_info["original_message_id"])
            await message.reply("✅ **تم إرسال ردك للمستخدم بنجاح.**")
            del data_store.forwarded_message_links[replied_to_msg_id]
        except Exception as e:
            await message.reply(f"❌ **فشل إرسال الرد.**\nالخطأ: {e}")

# --- Central Callback Query Handler ---
async def callbacks_cmd(cq: types.CallbackQuery, state: FSMContext):
    await cq.answer()
    await state.finish()
    d = cq.data
    cfg = data_store.bot_data['bot_settings']

    # --- Instant Actions ---
    if d == "close_panel": await cq.message.delete(); return
    if d == "back_to_main": await cq.message.edit_text("🔧 **لوحة التحكم الإدارية**\n\nاختر الإجراء المطلوب:", reply_markup=create_admin_panel()); return
    
    if d == "admin_stats":
        stats = (f"📊 **إحصائيات البوت:**\n\n"
                 f"👥 المستخدمون: {len(data_store.bot_data['users'])}\n"
                 f"🚫 المحظورون: {len(data_store.bot_data['banned_users'])}\n"
                 f"💬 الردود المبرمجة: {len(data_store.bot_data['dynamic_replies'])}\n"
                 f"💡 التذكيرات: {len(data_store.bot_data['reminders'])}")
        await cq.message.edit_text(stats, reply_markup=back_kb()); return
    
    if d == "deploy_status":
        uptime = datetime.datetime.now() - data_store.start_time
        status = (f"🚀 **حالة النشر:**\n\n✅ نشط ومستقر\n⏰ مدة التشغيل: {str(uptime).split('.')[0]}")
        await cq.message.edit_text(status, reply_markup=back_kb()); return

    # --- Toggles ---
    if d == "toggle_maintenance":
        cfg['maintenance_mode'] = not cfg.get('maintenance_mode', False)
        status = "في وضع الصيانة" if cfg['maintenance_mode'] else "يعمل بشكل طبيعي"
        await cq.answer(f"✅ تم تغيير حالة البوت إلى: {status}", show_alert=True)
    elif d == "toggle_protection":
        cfg['content_protection'] = not cfg.get('content_protection', False)
        status = "مفعلة" if cfg['content_protection'] else "معطلة"
        await cq.answer(f"✅ تم تغيير حالة حماية المحتوى إلى: {status}", show_alert=True)
    
    if d in ["toggle_maintenance", "toggle_protection"]:
        data_store.save_data()
        await cq.message.edit_text("🛡️ **إعدادات الحماية والأمان**", reply_markup=get_menu_keyboard("admin_security")); return

    if d == "clear_spam_cache":
        count = len(data_store.user_message_count) + len(data_store.silenced_users)
        data_store.user_message_count.clear(); data_store.silenced_users.clear()
        await cq.answer(f"✅ تم مسح {count} سجل من ذاكرة الحماية.", show_alert=True); return

    # --- Sub-menus & Info Displays ---
    menus = {
        "admin_dyn_replies": "📝 **إدارة الردود الديناميكية**", "admin_reminders": "💭 **إدارة التذكيرات**",
        "admin_channel": "📢 **إدارة منشورات القناة**", "admin_ban": "🚫 **إدارة الحظر**",
        "admin_customize_ui": "🎨 **تخصيص واجهة البوت**", "admin_security": "🛡️ **إعدادات الحماية والأمان**",
        "admin_memory_management": "🧠 **إدارة الذاكرة**", "admin_channel_settings": "⚙️ **إعدادات القناة**",
        "media_settings": f"🖼️ **إدارة الوسائط**\n\nالأنواع المسموح بها: `{', '.join(cfg.get('allowed_media_types', []))}`",
        "spam_settings": f"🔧 **منع التكرار**\n\n- الحد: {cfg.get('spam_message_limit')} رسائل\n- خلال: {cfg.get('spam_time_window')} ثانية",
        "slow_mode_settings": f"⏳ **التباطؤ**\n\n- الانتظار: {cfg.get('slow_mode_seconds')} ثواني"
    }
    if d in menus:
        await cq.message.edit_text(f"{menus[d]}\n\nاختر الإجراء المطلوب:", reply_markup=get_menu_keyboard(d)); return

    # --- Display Lists ---
    lists = {
        "show_dyn_replies": ("📝 **الردود المبرمجة:**", "admin_dyn_replies", [f"🔹 `{k}`" for k in data_store.bot_data['dynamic_replies']]),
        "show_reminders": ("💭 **التذكيرات:**", "admin_reminders", [f"{i+1}. {r[:40]}..." for i, r in enumerate(data_store.bot_data['reminders'])]),
        "show_channel_msgs": ("📢 **رسائل القناة التلقائية:**", "admin_channel", [f"{i+1}. {m[:40]}..." for i, m in enumerate(data_store.bot_data['channel_messages'])]),
        "show_banned": ("🚫 **المحظورون:**", "admin_ban", [f"`{uid}`" for uid in data_store.bot_data['banned_users']])
    }
    if d in lists:
        title, back_cb, items = lists[d]
        text = title + "\n\n" + ("\n".join(items) if items else "لا يوجد شيء لعرضه.")
        await cq.message.edit_text(text, reply_markup=back_kb(back_cb)); return

    # --- FSM State Triggers ---
    prompts = {
        "add_dyn_reply": ("📝 أرسل **الكلمة المفتاحية**:", AdminStates.waiting_for_dyn_reply_keyword),
        "delete_dyn_reply": ("🗑️ أرسل الكلمة المفتاحية للحذف:", AdminStates.waiting_for_dyn_reply_delete),
        "add_reminder": ("💭 أرسل نص التذكير الجديد:", AdminStates.waiting_for_new_reminder),
        "delete_reminder": ("🗑️ أرسل رقم التذكير للحذف:", AdminStates.waiting_for_delete_reminder),
        "add_channel_msg": ("➕ أرسل نص الرسالة التلقائية للقناة:", AdminStates.waiting_for_new_channel_msg),
        "delete_channel_msg": ("🗑️ أرسل رقم الرسالة للحذف:", AdminStates.waiting_for_delete_channel_msg),
        "instant_channel_post": ("📤 أرسل الرسالة للنشر الفوري:", AdminStates.waiting_for_instant_channel_post),
        "schedule_post": ("⏰ أرسل **نص الرسالة** للجدولة:", AdminStates.waiting_for_scheduled_post_text),
        "ban_user": ("🚫 أرسل ID المستخدم للحظر:", AdminStates.waiting_for_ban_id),
        "unban_user": ("✅ أرسل ID المستخدم لإلغاء الحظر:", AdminStates.waiting_for_unban_id),
        "edit_date_button": ("✏️ أرسل الاسم الجديد لزر التاريخ:", AdminStates.waiting_for_date_button_label),
        "edit_time_button": ("✏️ أرسل الاسم الجديد لزر الساعة:", AdminStates.waiting_for_time_button_label),
        "edit_reminder_button": ("✏️ أرسل الاسم الجديد لزر التذكير:", AdminStates.waiting_for_reminder_button_label),
        "edit_welcome_msg": ("👋 أرسل نص الترحيب الجديد:", AdminStates.waiting_for_welcome_message),
        "edit_reply_msg": ("💬 أرسل نص الرد التلقائي الجديد:", AdminStates.waiting_for_reply_message),
        "clear_user_data": ("🗑️ أرسل ID المستخدم لمسح بياناته:", AdminStates.waiting_for_clear_user_id),
        "set_channel_id": ("🆔 أرسل ID القناة الجديد:", AdminStates.waiting_for_channel_id),
        "set_schedule_interval": ("⏰ أرسل فترة النشر التلقائي بالساعات:", AdminStates.waiting_for_schedule_interval),
        "edit_maintenance_message": ("✍️ أرسل رسالة الصيانة الجديدة:", AdminStates.waiting_for_maintenance_message),
        "set_spam_limit": ("🔢 أرسل الحد الأقصى الجديد للرسائل:", AdminStates.waiting_for_spam_limit),
        "set_spam_window": ("⏱️ أرسل الفترة الزمنية الجديدة بالثواني:", AdminStates.waiting_for_spam_window),
        "set_slow_mode": ("⏳ أرسل فترة التباطؤ الجديدة بالثواني (0 للإلغاء):", AdminStates.waiting_for_slow_mode),
        "add_media_type": ("➕ أرسل نوع الوسائط للسماح به (photo, video, link...):", AdminStates.waiting_for_add_media_type),
        "remove_media_type": ("➖ أرسل نوع الوسائط للمنع (photo, video...):", AdminStates.waiting_for_remove_media_type),
        "edit_media_reject_message": ("✍️ أرسل رسالة رفض الوسائط الجديدة:", AdminStates.waiting_for_media_reject_message),
    }
    if d in prompts:
        prompt_text, state_to_set = prompts[d]
        await state.set_state(state_to_set)
        await cq.message.edit_text(f"{prompt_text}\n\nلإلغاء العملية، أرسل /cancel."); return

# --- FSM Handlers ---

async def cancel_cmd(m, s): await s.finish(); await m.reply("✅ تم إلغاء العملية.", reply_markup=create_admin_panel())

# --- Text/Numeric Input Handlers ---
async def process_text_input(m, s, data_key, success_msg, is_list=False, kb_info=None):
    val = m.text.strip(); target = data_store.bot_data
    for k in data_key[:-1]: target = target.setdefault(k, {})
    if is_list: target.setdefault(data_key[-1], []).append(val)
    else: target[data_key[-1]] = val
    data_store.save_data()
    reply_markup = add_another_kb(kb_info[0], kb_info[1]) if kb_info else create_admin_panel()
    await m.reply(success_msg.format(value=val), reply_markup=reply_markup)
    await s.finish()

async def process_numeric_input(m, s, data_key, success_msg):
    try:
        val = int(m.text.strip()); target = data_store.bot_data['bot_settings']
        target[data_key] = val
        data_store.save_data()
        await m.reply(success_msg.format(value=val), reply_markup=create_admin_panel())
    except ValueError: await m.reply("❌ الرجاء إرسال رقم صحيح.")
    await s.finish()

# --- Deletion Handlers ---
async def process_delete_by_index(m, s, data_key, item_name, kb_info):
    try:
        idx = int(m.text.strip()) - 1; lst = data_store.bot_data[data_key]
        if 0 <= idx < len(lst):
            removed = lst.pop(idx); data_store.save_data()
            await m.reply(f"✅ تم حذف {item_name}:\n`{removed}`", reply_markup=add_another_kb(kb_info[0], kb_info[1]))
        else: await m.reply(f"❌ رقم غير صالح. (1 - {len(lst)})")
    except (ValueError, IndexError): await m.reply("❌ الرجاء إرسال رقم صحيح.")
    await s.finish()

# --- Specific FSM Handlers ---
async def dyn_reply_keyword(m, s): await s.update_data(keyword=m.text.strip()); await m.reply("👍 الآن أرسل **المحتوى**."); await AdminStates.next()
async def dyn_reply_content(m, s):
    data = await s.get_data(); keyword, content = data['keyword'], m.text
    data_store.bot_data['dynamic_replies'][keyword] = content; data_store.save_data()
    await m.reply(f"✅ **تمت برمجة الرد!**", reply_markup=add_another_kb("add_dyn_reply", "admin_dyn_replies"))
    await s.finish()

async def dyn_reply_delete(m, s):
    keyword = m.text.strip()
    if keyword in data_store.bot_data['dynamic_replies']:
        del data_store.bot_data['dynamic_replies'][keyword]; data_store.save_data()
        await m.reply(f"✅ تم حذف الرد الخاص بـ `{keyword}`", reply_markup=add_another_kb("delete_dyn_reply", "admin_dyn_replies"))
    else: await m.reply(f"❌ لم يتم العثور على رد لهذه الكلمة.", reply_markup=create_admin_panel())
    await s.finish()

async def scheduled_post_text(m, s): await s.update_data(post_text=m.text.strip()); await m.reply("👍 الآن أرسل وقت الإرسال:\n`YYYY-MM-DD HH:MM` (بتوقيت UTC)"); await AdminStates.next()
async def scheduled_post_datetime(m, s):
    try:
        dt_str = m.text.strip(); send_at = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M"); send_at_utc = pytz.utc.localize(send_at)
        data = await s.get_data(); post_text = data['post_text']
        channel_id = data_store.bot_data['bot_settings'].get('channel_id')
        if not channel_id: await m.reply("❌ **خطأ:** يجب تحديد ID القناة أولاً.", reply_markup=create_admin_panel()); await s.finish(); return
        new_post = {"text": post_text, "channel_id": channel_id, "send_at_iso": send_at_utc.isoformat()}
        data_store.bot_data.setdefault("scheduled_posts", []).append(new_post); data_store.save_data()
        await m.reply(f"✅ **تمت جدولة الرسالة!**", reply_markup=add_another_kb("schedule_post", "admin_channel"))
    except ValueError: await m.reply("❌ **تنسيق التاريخ خاطئ!**")
    await s.finish()

async def ban_unban_user(m, s, ban):
    try:
        user_id = int(m.text.strip()); b_list = data_store.bot_data['banned_users']
        if ban:
            if user_id not in b_list: b_list.append(user_id)
            await m.reply(f"🚫 تم حظر `{user_id}`.", reply_markup=create_admin_panel())
        else:
            if user_id in b_list: b_list.remove(user_id); await m.reply(f"✅ تم إلغاء حظر `{user_id}`.")
            else: await m.reply(f"ℹ️ المستخدم `{user_id}` غير محظور أصلاً.")
        data_store.save_data()
    except ValueError: await m.reply("❌ ID غير صالح.")
    await s.finish()

async def broadcast_msg(m, s):
    succ, fail = 0, 0
    await m.reply(f"📤 بدء الإرسال لـ {len(data_store.bot_data['users'])} مستخدم...")
    for uid in data_store.bot_data['users']:
        try: await m.copy_to(uid); succ += 1; await asyncio.sleep(0.05)
        except: fail += 1
    await m.reply(f"✅ **اكتمل الإرسال:** نجح: {succ}, فشل: {fail}", reply_markup=create_admin_panel())
    await s.finish()

async def clear_user(m, s):
    try:
        uid = int(m.text.strip()); c = 0
        if uid in data_store.user_message_count: del data_store.user_message_count[uid]; c += 1
        if uid in data_store.silenced_users: del data_store.silenced_users[uid]; c += 1
        await m.reply(f"✅ تم مسح {c} سجل حماية للمستخدم `{uid}`.", reply_markup=create_admin_panel())
    except ValueError: await m.reply("❌ ID غير صالح.")
    await s.finish()

async def set_timezone(m, s):
    try:
        tz = m.text.strip(); pytz.timezone(tz); data_store.bot_data['ui_config']['timezone'] = tz; data_store.save_data()
        await m.reply(f"✅ تم تحديث المنطقة الزمنية إلى: `{tz}`", reply_markup=create_admin_panel())
    except pytz.UnknownTimeZoneError: await m.reply("❌ **منطقة زمنية غير صالحة!**\nمثال: `Asia/Aden`")
    await s.finish()
    
# --- Handler Registration ---
def register_admin_handlers(dp: Dispatcher):
    f = lambda m: m.from_user.id == ADMIN_CHAT_ID
    
    dp.register_message_handler(admin_panel_cmd, f, commands=['admin'], state="*")
    dp.register_message_handler(admin_reply_cmd, f, is_reply=True, content_types=types.ContentTypes.ANY, state="*")
    dp.register_callback_query_handler(callbacks_cmd, f, state="*")
    dp.register_message_handler(cancel_cmd, f, commands=['cancel'], state='*')

    # Register all FSM handlers
    dp.register_message_handler(dyn_reply_keyword, f, state=AdminStates.waiting_for_dyn_reply_keyword)
    dp.register_message_handler(dyn_reply_content, f, state=AdminStates.waiting_for_dyn_reply_content)
    dp.register_message_handler(dyn_reply_delete, f, state=AdminStates.waiting_for_dyn_reply_delete)
    
    dp.register_message_handler(lambda m,s: process_text_input(m,s,['reminders'],"✅ تم إضافة التذكير.",True,("add_reminder","admin_reminders")), f, state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(lambda m,s: process_delete_by_index(m,s, "reminders", "التذكير", ("delete_reminder", "admin_reminders")), f, state=AdminStates.waiting_for_delete_reminder)

    dp.register_message_handler(lambda m,s: process_text_input(m,s,['channel_messages'],"✅ تم إضافة رسالة القناة.",True,("add_channel_msg","admin_channel")), f, state=AdminStates.waiting_for_new_channel_msg)
    dp.register_message_handler(lambda m,s: process_delete_by_index(m,s, "channel_messages", "الرسالة", ("delete_channel_msg", "admin_channel")), f, state=AdminStates.waiting_for_delete_channel_msg)

    dp.register_message_handler(scheduled_post_text, f, state=AdminStates.waiting_for_scheduled_post_text)
    dp.register_message_handler(scheduled_post_datetime, f, state=AdminStates.waiting_for_scheduled_post_datetime)

    dp.register_message_handler(lambda m,s: ban_unban_user(m,s,True), f, state=AdminStates.waiting_for_ban_id)
    dp.register_message_handler(lambda m,s: ban_unban_user(m,s,False), f, state=AdminStates.waiting_for_unban_id)
    dp.register_message_handler(broadcast_msg, f, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_broadcast_message)
    
    # UI Customization
    dp.register_message_handler(lambda m,s: process_text_input(m, s, ['ui_config', 'date_button_label'], "✅ تم تحديث اسم الزر."), f, state=AdminStates.waiting_for_date_button_label)
    dp.register_message_handler(lambda m,s: process_text_input(m, s, ['ui_config', 'time_button_label'], "✅ تم تحديث اسم الزر."), f, state=AdminStates.waiting_for_time_button_label)
    dp.register_message_handler(lambda m,s: process_text_input(m, s, ['ui_config', 'reminder_button_label'], "✅ تم تحديث اسم الزر."), f, state=AdminStates.waiting_for_reminder_button_label)
    dp.register_message_handler(set_timezone, f, state=AdminStates.waiting_for_timezone)
    dp.register_message_handler(lambda m,s: process_text_input(m, s, ['bot_settings', 'welcome_message'], "✅ تم تحديث رسالة الترحيب."), f, state=AdminStates.waiting_for_welcome_message)
    dp.register_message_handler(lambda m,s: process_text_input(m, s, ['bot_settings', 'reply_message'], "✅ تم تحديث رسالة الرد."), f, state=AdminStates.waiting_for_reply_message)
    
    # Memory
    dp.register_message_handler(clear_user, f, state=AdminStates.waiting_for_clear_user_id)
    
    # Channel Settings
    dp.register_message_handler(lambda m,s: process_text_input(m, s, ['bot_settings', 'channel_id'], "✅ تم تحديث ID القناة."), f, state=AdminStates.waiting_for_channel_id)
    dp.register_message_handler(lambda m,s: process_numeric_input(m, s, 'schedule_interval_seconds', "✅ تم تحديث فترة النشر."), f, state=AdminStates.waiting_for_schedule_interval)

    # Security
    dp.register_message_handler(lambda m,s: process_text_input(m,s,['bot_settings','maintenance_message'],"✅ تم تحديث رسالة الصيانة."), f, state=AdminStates.waiting_for_maintenance_message)
    dp.register_message_handler(lambda m,s: process_numeric_input(m,s,'spam_message_limit',"✅ تم تحديث حد الرسائل."), f, state=AdminStates.waiting_for_spam_limit)
    dp.register_message_handler(lambda m,s: process_numeric_input(m,s,'spam_time_window',"✅ تم تحديث الفترة الزمنية."), f, state=AdminStates.waiting_for_spam_window)
    dp.register_message_handler(lambda m,s: process_numeric_input(m,s,'slow_mode_seconds',"✅ تم تحديث فترة التباطؤ."), f, state=AdminStates.waiting_for_slow_mode)
    dp.register_message_handler(lambda m,s: process_text_input(m,s,['bot_settings','allowed_media_types'],"✅ تم السماح بالنوع: {value}",True), f, state=AdminStates.waiting_for_add_media_type)
    dp.register_message_handler(lambda m,s: process_text_input(m,s,['bot_settings','media_reject_message'],"✅ تم تحديث رسالة الرفض."), f, state=AdminStates.waiting_for_media_reject_message)
    
    @dp.message_handler(f, state=AdminStates.waiting_for_remove_media_type)
    async def process_remove_media_type(m: types.Message, state: FSMContext):
        media_type = m.text.strip()
        if media_type in cfg['allowed_media_types']:
            cfg['allowed_media_types'].remove(media_type)
            data_store.save_data()
            await m.reply(f"✅ تم منع النوع: `{media_type}`", reply_markup=create_admin_panel())
        else:
            await m.reply(f"❌ النوع `{media_type}` غير موجود في القائمة أصلاً.")
        await state.finish()


