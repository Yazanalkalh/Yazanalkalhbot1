import asyncio, datetime, pytz
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
import data_store
from keyboards.inline import create_admin_panel, get_menu_keyboard, back_kb, add_another_kb

# --- Main Admin Command Handlers ---
async def admin_panel_cmd(m: types.Message, state: FSMContext):
    if await state.get_state() is not None:
        await state.finish()
    await m.reply("🔧 **لوحة التحكم الإدارية**", reply_markup=create_admin_panel())

async def admin_reply_cmd(m: types.Message, state: FSMContext):
    if not m.reply_to_message: return
    link = data_store.forwarded_message_links.get(m.reply_to_message.message_id)
    if link:
        try:
            await m.copy_to(link["user_id"], reply_to_message_id=link["original_message_id"])
            await m.reply("✅ **تم إرسال الرد بنجاح.**")
            if m.reply_to_message.message_id in data_store.forwarded_message_links:
                del data_store.forwarded_message_links[m.reply_to_message.message_id]
        except Exception as e: await m.reply(f"❌ **فشل إرسال الرد:** {e}")

# --- Central Callback Query Handler ---
async def callbacks_cmd(cq: types.CallbackQuery, state: FSMContext):
    await cq.answer()
    if await state.get_state() is not None: await state.finish()
    d = cq.data
    cfg = data_store.bot_data['bot_settings']
    
    # Instant Actions
    if d == "close_panel": await cq.message.delete(); return
    if d == "back_to_main": await cq.message.edit_text("🔧 **لوحة التحكم الإدارية**", reply_markup=create_admin_panel()); return
    
    if d == "admin_stats":
        stats_text = (f"📊 **إحصائيات البوت:**\n\n"
                      f"👥 المستخدمون: {len(data_store.bot_data['users'])}\n"
                      f"🚫 المحظورون: {len(data_store.bot_data['banned_users'])}\n"
                      f"💬 الردود المبرمجة: {len(data_store.bot_data['dynamic_replies'])}\n"
                      f"💡 التذكيرات: {len(data_store.bot_data['reminders'])}")
        await cq.message.edit_text(stats_text, reply_markup=back_kb()); return
    
    if d == "deploy_status":
        uptime = datetime.datetime.now() - data_store.start_time
        status_text = f"🚀 **حالة النشر:**\n\n✅ نشط ومستقر\n⏰ مدة التشغيل: {str(uptime).split('.')[0]}"
        await cq.message.edit_text(status_text, reply_markup=back_kb()); return

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
        count = len(data_store.user_last_message_time)
        data_store.user_last_message_time.clear()
        await cq.answer(f"✅ تم مسح {count} سجل من ذاكرة التباطؤ.", show_alert=True); return
    
    # Sub-menus & Info Displays
    menus = {
        "admin_dyn_replies": "📝 **الردود الديناميكية**", "admin_reminders": "💭 **إدارة التذكيرات**",
        "admin_channel": "📢 **منشورات القناة**", "admin_ban": "🚫 **إدارة الحظر**",
        "admin_broadcast": f"📤 **النشر للجميع** ({len(data_store.bot_data['users'])} مستخدم)",
        "admin_customize_ui": "🎨 **تخصيص الواجهة**", "admin_security": "🛡️ **الحماية والأمان**",
        "admin_memory_management": "🧠 **إدارة الذاكرة**", "admin_channel_settings": "⚙️ **إعدادات القناة**",
        "media_settings": f"🖼️ **إدارة الوسائط**\n\nمسموح بـ: `{', '.join(cfg['allowed_media_types'])}`",
        "spam_settings": f"🔧 **منع التكرار**\n\n- الحد: {cfg['spam_message_limit']} رسائل / {cfg['spam_time_window']} ثانية",
        "slow_mode_settings": f"⏳ **التباطؤ**\n\n- الانتظار: {cfg['slow_mode_seconds']} ثواني"
    }
    if d in menus:
        await cq.message.edit_text(f"{menus[d]}\n\nاختر الإجراء:", reply_markup=get_menu_keyboard(d)); return

    # Display Lists
    lists = {
        "show_dyn_replies": ("📝 **الردود المبرمجة:**", "admin_dyn_replies", [f"▫️ `{k}`" for k in data_store.bot_data['dynamic_replies']]),
        "show_reminders": ("💭 **التذكيرات:**", "admin_reminders", [f"{i+1}. {r[:40]}..." for i, r in enumerate(data_store.bot_data['reminders'])]),
        "show_channel_msgs": ("📢 **الرسائل التلقائية:**", "admin_channel", [f"{i+1}. {m[:40]}..." for i, m in enumerate(data_store.bot_data['channel_messages'])]),
        "show_banned": ("🚫 **المحظورون:**", "admin_ban", [f"`{uid}`" for uid in data_store.bot_data['banned_users']])
    }
    if d in lists:
        title, back_cb, items = lists[d]
        text = title + "\n\n" + ("\n".join(items) if items else "لا يوجد شيء لعرضه.")
        await cq.message.edit_text(text, reply_markup=back_kb(back_cb)); return

    # FSM State Triggers
    prompts = {
        "add_dyn_reply": ("📝 أرسل **الكلمة المفتاحية**:", AdminStates.waiting_for_dyn_reply_keyword),
        "delete_dyn_reply": ("🗑️ أرسل الكلمة المفتاحية للحذف:", AdminStates.waiting_for_dyn_reply_delete),
        "add_reminder": ("💭 أرسل نص التذكير:", AdminStates.waiting_for_new_reminder),
        "delete_reminder": ("🗑️ أرسل رقم التذكير للحذف:", AdminStates.waiting_for_delete_reminder),
        "add_channel_msg": ("➕ أرسل نص الرسالة التلقائية:", AdminStates.waiting_for_new_channel_msg),
        "delete_channel_msg": ("🗑️ أرسل رقم الرسالة للحذف:", AdminStates.waiting_for_delete_channel_msg),
        "instant_channel_post": ("📤 أرسل الرسالة للنشر الفوري:", AdminStates.waiting_for_instant_channel_post),
        "schedule_post": ("⏰ أرسل **نص الرسالة** للجدولة:", AdminStates.waiting_for_scheduled_post_text),
        "ban_user": ("🚫 أرسل ID المستخدم للحظر:", AdminStates.waiting_for_ban_id),
        "unban_user": ("✅ أرسل ID المستخدم لإلغاء الحظر:", AdminStates.waiting_for_unban_id),
        "send_broadcast": ("📤 أرسل رسالتك للجميع:", AdminStates.waiting_for_broadcast_message),
        "edit_date_button": ("✏️ أرسل الاسم الجديد لزر التاريخ:", AdminStates.waiting_for_date_button_label),
        "edit_time_button": ("✏️ أرسل الاسم الجديد لزر الساعة:", AdminStates.waiting_for_time_button_label),
        "edit_reminder_button": ("✏️ أرسل الاسم الجديد لزر التذكير:", AdminStates.waiting_for_reminder_button_label),
        "set_timezone": ("🌍 أرسل المنطقة الزمنية (مثال: Asia/Aden):", AdminStates.waiting_for_timezone),
        "edit_welcome_msg": ("👋 أرسل نص الترحيب الجديد:", AdminStates.waiting_for_welcome_message),
        "edit_reply_msg": ("💬 أرسل نص الرد التلقائي الجديد:", AdminStates.waiting_for_reply_message),
        "clear_user_data": ("🗑️ أرسل ID المستخدم لمسح بياناته:", AdminStates.waiting_for_clear_user_id),
        "set_channel_id": ("🆔 أرسل ID القناة الجديد:", AdminStates.waiting_for_channel_id),
        "set_schedule_interval": ("⏰ أرسل فترة النشر بالساعات:", AdminStates.waiting_for_schedule_interval),
        "set_spam_limit": ("🔢 أرسل حد الرسائل:", AdminStates.waiting_for_spam_limit),
        "set_spam_window": ("⏱️ أرسل الفترة بالثواني:", AdminStates.waiting_for_spam_window),
        "set_slow_mode": ("⏳ أرسل فترة التباطؤ بالثواني:", AdminStates.waiting_for_slow_mode),
        "add_media_type": ("➕ أرسل نوع الوسائط (photo, video...):", AdminStates.waiting_for_add_media_type),
        "remove_media_type": ("➖ أرسل نوع الوسائط للمنع:", AdminStates.waiting_for_remove_media_type),
        "edit_media_reject_message": ("✍️ أرسل رسالة الرفض الجديدة:", AdminStates.waiting_for_media_reject_message),
    }
    if d in prompts:
        prompt, state_obj = prompts[d]
        await state.set_state(state_obj)
        await cq.message.edit_text(f"{prompt}\n\nلإلغاء العملية، أرسل /cancel."); return

# --- FSM Handlers ---
async def cancel_cmd(m: types.Message, s: FSMContext):
    await s.finish()
    await m.reply("✅ تم إلغاء العملية.", reply_markup=create_admin_panel())

async def process_text_input(m: types.Message, s: FSMContext, data_key: list, success_msg: str, is_list=False, kb_info=None):
    val = m.text.strip()
    target = data_store.bot_data
    for k in data_key[:-1]:
        target = target.setdefault(k, {})
    
    if is_list:
        target.setdefault(data_key[-1], []).append(val)
    else:
        target[data_key[-1]] = val
    
    data_store.save_data()
    reply_markup = add_another_kb(*kb_info) if kb_info else create_admin_panel()
    await m.reply(success_msg.format(value=val), reply_markup=reply_markup)
    await s.finish()

async def process_numeric_input(m: types.Message, s: FSMContext, data_key: str, success_msg: str):
    try:
        val = int(m.text.strip())
        data_store.bot_data['bot_settings'][data_key] = val
        data_store.save_data()
        await m.reply(success_msg.format(value=val), reply_markup=create_admin_panel())
    except ValueError:
        await m.reply("❌ الرجاء إرسال رقم صحيح.")
    await s.finish()

async def process_delete_by_index(m: types.Message, s: FSMContext, data_key: str, item_name: str, kb_info: tuple):
    try:
        idx = int(m.text.strip()) - 1
        lst = data_store.bot_data[data_key]
        if 0 <= idx < len(lst):
            removed = lst.pop(idx)
            data_store.save_data()
            await m.reply(f"✅ تم حذف {item_name}:\n`{removed}`", reply_markup=add_another_kb(*kb_info))
        else:
            await m.reply(f"❌ رقم غير صالح. (1 - {len(lst)})")
    except (ValueError, IndexError):
        await m.reply("❌ الرجاء إرسال رقم صحيح.")
    await s.finish()

async def dyn_reply_keyword(m: types.Message, s: FSMContext):
    await s.update_data(keyword=m.text.strip())
    await m.reply("👍 الآن أرسل **المحتوى**.")
    await AdminStates.next()

async def dyn_reply_content(m: types.Message, s: FSMContext):
    data = await s.get_data()
    keyword, content = data['keyword'], m.text
    data_store.bot_data['dynamic_replies'][keyword] = content
    data_store.save_data()
    await m.reply("✅ **تمت برمجة الرد!**", reply_markup=add_another_kb("add_dyn_reply", "admin_dyn_replies"))
    await s.finish()

async def dyn_reply_delete(m: types.Message, s: FSMContext):
    keyword = m.text.strip()
    if keyword in data_store.bot_data['dynamic_replies']:
        del data_store.bot_data['dynamic_replies'][keyword]
        data_store.save_data()
        await m.reply(f"✅ تم حذف الرد الخاص بـ `{keyword}`", reply_markup=add_another_kb("delete_dyn_reply", "admin_dyn_replies"))
    else:
        await m.reply("❌ لم يتم العثور على رد لهذه الكلمة.", reply_markup=create_admin_panel())
    await s.finish()

async def scheduled_post_text(m: types.Message, s: FSMContext):
    await s.update_data(post_text=m.text.strip())
    await m.reply("👍 الآن أرسل وقت الإرسال:\n`YYYY-MM-DD HH:MM` (بتوقيت UTC)")
    await AdminStates.next()

async def scheduled_post_datetime(m: types.Message, s: FSMContext):
    try:
        dt_str = m.text.strip()
        send_at_utc = pytz.utc.localize(datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M"))
        data = await s.get_data()
        post_text = data['post_text']
        channel_id = data_store.bot_data['bot_settings']['channel_id']
        if not channel_id:
            await m.reply("❌ **خطأ:** يجب تحديد ID القناة أولاً.")
            await s.finish()
            return
        new_post = {"text": post_text, "channel_id": channel_id, "send_at_iso": send_at_utc.isoformat()}
        data_store.bot_data.setdefault("scheduled_posts", []).append(new_post)
        data_store.save_data()
        await m.reply("✅ **تمت جدولة الرسالة!**", reply_markup=add_another_kb("schedule_post", "admin_channel"))
    except ValueError:
        await m.reply("❌ **تنسيق التاريخ خاطئ!**")
    await s.finish()

async def ban_unban_user(m: types.Message, s: FSMContext, ban: bool):
    try:
        user_id = int(m.text.strip())
        b_list = data_store.bot_data['banned_users']
        if ban:
            if user_id not in b_list:
                b_list.append(user_id)
            await m.reply(f"🚫 تم حظر `{user_id}`.", reply_markup=create_admin_panel())
        else:
            if user_id in b_list:
                b_list.remove(user_id)
                await m.reply(f"✅ تم إلغاء حظر `{user_id}`.")
            else:
                await m.reply(f"ℹ️ المستخدم `{user_id}` غير محظور أصلاً.")
        data_store.save_data()
    except ValueError:
        await m.reply("❌ ID غير صالح.")
    await s.finish()

async def broadcast_msg(m: types.Message, s: FSMContext):
    succ, fail = 0, 0
    await m.reply(f"📤 بدء الإرسال لـ {len(data_store.bot_data['users'])} مستخدم...")
    for uid in data_store.bot_data['users']:
        try:
            await m.copy_to(uid)
            succ += 1
            await asyncio.sleep(0.05)
        except:
            fail += 1
    await m.reply(f"✅ **اكتمل الإرسال:** نجح: {succ}, فشل: {fail}", reply_markup=create_admin_panel())
    await s.finish()

async def clear_user(m: types.Message, s: FSMContext):
    try:
        uid = int(m.text.strip())
        c = 0
        if uid in data_store.user_last_message_time:
            del data_store.user_last_message_time[uid]
            c += 1
        await m.reply(f"✅ تم مسح {c} سجل حماية للمستخدم `{uid}`.", reply_markup=create_admin_panel())
    except ValueError:
        await m.reply("❌ ID غير صالح.")
    await s.finish()

async def set_timezone(m: types.Message, s: FSMContext):
    try:
        tz = m.text.strip()
        pytz.timezone(tz)
        data_store.bot_data['ui_config']['timezone'] = tz
        data_store.save_data()
        await m.reply(f"✅ تم تحديث المنطقة الزمنية إلى: `{tz}`", reply_markup=create_admin_panel())
    except pytz.UnknownTimeZoneError:
        await m.reply("❌ **منطقة زمنية غير صالحة!**\nمثال: `Asia/Aden`")
    await s.finish()

async def remove_media_type(m: types.Message, s: FSMContext):
    media_type = m.text.strip()
    allowed = data_store.bot_data['bot_settings']['allowed_media_types']
    if media_type in allowed and media_type != 'text': # Prevent removing 'text'
        allowed.remove(media_type)
        data_store.save_data()
        await m.reply(f"✅ تم منع النوع: `{media_type}`", reply_markup=create_admin_panel())
    elif media_type == 'text':
        await m.reply("❌ لا يمكن منع الرسائل النصية.")
    else:
        await m.reply(f"❌ النوع `{media_type}` غير مسموح به أصلاً.")
    await s.finish()

# --- Handler Registration ---
def register_admin_handlers(dp: Dispatcher):
    # THE CRITICAL FIX IS HERE
    f = lambda msg, **kwargs: msg.from_user.id == ADMIN_CHAT_ID
    
    # Main Commands
    dp.register_message_handler(admin_panel_cmd, f, commands=['admin'], state="*")
    dp.register_message_handler(admin_reply_cmd, f, is_reply=True, content_types=types.ContentTypes.ANY, state="*")
    dp.register_callback_query_handler(callbacks_cmd, f, state="*")
    dp.register_message_handler(cancel_cmd, f, commands=['cancel'], state='*')

    # FSM Handlers are now registered with the correct filter
    dp.register_message_handler(dyn_reply_keyword, f, state=AdminStates.waiting_for_dyn_reply_keyword)
    dp.register_message_handler(dyn_reply_content, f, content_types=types.ContentTypes.TEXT, state=AdminStates.waiting_for_dyn_reply_content)
    dp.register_message_handler(dyn_reply_delete, f, state=AdminStates.waiting_for_dyn_reply_delete)
    
    dp.register_message_handler(process_text_input, f, state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(process_delete_by_index, f, state=AdminStates.waiting_for_delete_reminder)

    dp.register_message_handler(process_text_input, f, state=AdminStates.waiting_for_new_channel_msg)
    dp.register_message_handler(process_delete_by_index, f, state=AdminStates.waiting_for_delete_channel_msg)
    
    async def instant_post_handler(m: types.Message, s: FSMContext):
        channel_id = data_store.bot_data['bot_settings'].get('channel_id')
        if channel_id:
            try:
                await bot.send_message(channel_id, m.text.strip())
                await m.reply("✅ تم النشر الفوري بنجاح.")
            except Exception as e:
                await m.reply(f"❌ فشل النشر: {e}")
        else:
            await m.reply("❌ يجب تحديد ID القناة أولاً.")
        await s.finish()
    dp.register_message_handler(instant_post_handler, f, state=AdminStates.waiting_for_instant_channel_post)

    dp.register_message_handler(scheduled_post_text, f, state=AdminStates.waiting_for_scheduled_post_text)
    dp.register_message_handler(scheduled_post_datetime, f, state=AdminStates.waiting_for_scheduled_post_datetime)

    dp.register_message_handler(lambda m, s: ban_unban_user(m, s, True), f, state=AdminStates.waiting_for_ban_id)
    dp.register_message_handler(lambda m, s: ban_unban_user(m, s, False), f, state=AdminStates.waiting_for_unban_id)
    dp.register_message_handler(broadcast_msg, f, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_broadcast_message)
    
    # UI Customization
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['ui_config', 'date_button_label'], "✅ تم تحديث اسم الزر."), f, state=AdminStates.waiting_for_date_button_label)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['ui_config', 'time_button_label'], "✅ تم تحديث اسم الزر."), f, state=AdminStates.waiting_for_time_button_label)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['ui_config', 'reminder_button_label'], "✅ تم تحديث اسم الزر."), f, state=AdminStates.waiting_for_reminder_button_label)
    dp.register_message_handler(set_timezone, f, state=AdminStates.waiting_for_timezone)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['bot_settings', 'welcome_message'], "✅ تم تحديث رسالة الترحيب."), f, state=AdminStates.waiting_for_welcome_message)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['bot_settings', 'reply_message'], "✅ تم تحديث رسالة الرد."), f, state=AdminStates.waiting_for_reply_message)
    
    # Memory
    dp.register_message_handler(clear_user, f, state=AdminStates.waiting_for_clear_user_id)
    
    # Channel Settings
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['bot_settings', 'channel_id'], "✅ تم تحديث ID القناة."), f, state=AdminStates.waiting_for_channel_id)
    
    async def process_schedule_interval_handler(m: types.Message, s: FSMContext):
        try:
            hours = float(m.text.strip())
            seconds = int(hours * 3600)
            if seconds < 60:
                await m.reply("❌ أقل فترة هي 60 ثانية (0.016 ساعة).")
            else:
                data_store.bot_data['bot_settings']['schedule_interval_seconds'] = seconds
                data_store.save_data()
                await m.reply(f"✅ تم تحديث فترة النشر التلقائي إلى كل {hours} ساعة.", reply_markup=create_admin_panel())
        except ValueError:
            await m.reply("❌ الرجاء إرسال رقم صحيح.")
        await s.finish()
    dp.register_message_handler(process_schedule_interval_handler, f, state=AdminStates.waiting_for_schedule_interval)

    # Security
    dp.register_message_handler(lambda m, s: process_numeric_input(m, s, 'spam_message_limit', "✅ تم تحديث حد الرسائل."), f, state=AdminStates.waiting_for_spam_limit)
    dp.register_message_handler(lambda m, s: process_numeric_input(m, s, 'spam_time_window', "✅ تم تحديث الفترة الزمنية."), f, state=AdminStates.waiting_for_spam_window)
    dp.register_message_handler(lambda m, s: process_numeric_input(m, s, 'slow_mode_seconds', "✅ تم تحديث فترة التباطؤ."), f, state=AdminStates.waiting_for_slow_mode)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['bot_settings','allowed_media_types'],"✅ تم السماح بالنوع: {value}",True), f, state=AdminStates.waiting_for_add_media_type)
    dp.register_message_handler(remove_media_type, f, state=AdminStates.waiting_for_remove_media_type)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['bot_settings','media_reject_message'], "✅ تم تحديث رسالة الرفض."), f, state=AdminStates.waiting_for_media_reject_message)
