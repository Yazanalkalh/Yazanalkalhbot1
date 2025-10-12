from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
import data_store
from keyboards.inline.admin_keyboards import create_admin_panel, add_another_kb
from keyboards.inline.advanced_keyboards import create_advanced_panel
import pytz, datetime, asyncio, io
from utils.database import add_content_to_library, add_scheduled_post

# This is the final, definitive, and complete version of the FSM handlers file.
# It contains the logic for EVERY state in BOTH the /admin and /hijri panels.

def is_admin(message: types.Message):
    """A filter to check if the user is an admin."""
    return message.from_user.id == ADMIN_CHAT_ID

# --- Universal Handler ---
async def cancel_cmd(m: types.Message, state: FSMContext): 
    current_state_str = str(await state.get_state())
    if current_state_str:
        await state.finish()
        # Return to the correct panel based on the state's context
        if "force_channel_id" in current_state_str:
             await m.reply("✅ تم إلغاء العملية.", reply_markup=create_advanced_panel())
        else:
             await m.reply("✅ تم إلغاء العملية.", reply_markup=create_admin_panel())

# --- /admin Panel Handlers ---

async def dyn_reply_keyword_handler(m: types.Message, state: FSMContext):
    await state.update_data(keyword=m.text.strip())
    await m.reply("الآن أرسل المحتوى الرد✅.")
    await AdminStates.next()

async def dyn_reply_content_handler(m: types.Message, state: FSMContext):
    data = await state.get_data()
    keyword = data['keyword']
    content = m.html_text
    data_store.bot_data.setdefault('dynamic_replies', {})[keyword] = content
    data_store.save_data()
    await m.reply("✅ تمت إضافة الرد بنجاح!", reply_markup=add_another_kb("add_dyn_reply", "admin_dyn_replies"))
    await state.finish()

async def dyn_reply_delete_handler(m: types.Message, state: FSMContext):
    keyword = m.text.strip()
    if keyword in data_store.bot_data.get('dynamic_replies', {}):
        del data_store.bot_data['dynamic_replies'][keyword]
        data_store.save_data()
        await m.reply(f"✅ تم حذف الرد الخاص بـ `{keyword}`", reply_markup=add_another_kb("delete_dyn_reply", "admin_dyn_replies"))
    else:
        await m.reply("❌ لم يتم العثور على رد بهذا المفتاح.", reply_markup=create_admin_panel())
    await state.finish()

async def import_dyn_replies_handler(m: types.Message, state: FSMContext):
    if not m.document or not m.document.file_name.lower().endswith('.txt'):
        return await m.reply("❌ خطأ: الرجاء إرسال ملف نصي (.txt) فقط.")
    file_info = await bot.get_file(m.document.file_id)
    file_content_bytes = await bot.download_file(file_info.file_path)
    file_content = io.StringIO(file_content_bytes.getvalue().decode('utf-8'))
    success, fail = 0, 0
    for line in file_content.readlines():
        line = line.strip()
        if '|' in line:
            parts = line.split('|', 1)
            if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                data_store.bot_data.setdefault('dynamic_replies', {})[parts[0].strip()] = parts[1].strip()
                success += 1
            else: fail += 1
        elif line: fail += 1
    if success > 0: data_store.save_data()
    await m.reply(f"✅ اكتمل استيراد الردود!\n- ناجحة: {success}\n- فاشلة: {fail}", reply_markup=create_admin_panel())
    await state.finish()

async def add_reminder_handler(m: types.Message, state: FSMContext):
    reminder_text = m.text.strip()
    data_store.bot_data.setdefault('reminders', []).append(reminder_text)
    data_store.save_data()
    await m.reply("✅ تمت إضافة التذكير بنجاح!", reply_markup=add_another_kb("add_reminder", "admin_reminders"))
    await state.finish()

async def delete_reminder_handler(m: types.Message, state: FSMContext):
    try:
        idx = int(m.text.strip()) - 1
        reminders = data_store.bot_data.get('reminders', [])
        if 0 <= idx < len(reminders):
            removed = reminders.pop(idx)
            data_store.save_data()
            await m.reply(f"✅ تم حذف التذكير:\n`{removed}`", reply_markup=add_another_kb("delete_reminder", "admin_reminders"))
        else: await m.reply(f"❌ رقم غير صالح. (1 - {len(reminders)})")
    except (ValueError, IndexError): await m.reply("❌ إدخال خاطئ.")
    await state.finish()

async def import_reminders_handler(m: types.Message, state: FSMContext):
    if not m.document or not m.document.file_name.lower().endswith('.txt'):
        return await m.reply("❌ خطأ: الرجاء إرسال ملف نصي (.txt) فقط.")
    file_info = await bot.get_file(m.document.file_id)
    file_content_bytes = await bot.download_file(file_info.file_path)
    file_content = io.StringIO(file_content_bytes.getvalue().decode('utf-8'))
    success = 0
    for line in file_content.readlines():
        reminder = line.strip()
        if reminder:
            data_store.bot_data.setdefault('reminders', []).append(reminder)
            success += 1
    if success > 0: data_store.save_data()
    await m.reply(f"✅ اكتمل استيراد التذكيرات!\n- تم استيراد {success} تذكيرًا.", reply_markup=create_admin_panel())
    await state.finish()

async def ban_user_handler(m: types.Message, state: FSMContext):
    try:
        user_id = int(m.text.strip())
        b_list = data_store.bot_data.setdefault('banned_users', [])
        if user_id not in b_list:
            b_list.append(user_id)
            data_store.save_data()
        await m.reply(f"🚫 تم حظر `{user_id}`.", reply_markup=create_admin_panel())
    except ValueError: await m.reply("❌ ID غير صالح.")
    await state.finish()

async def unban_user_handler(m: types.Message, state: FSMContext):
    try:
        user_id = int(m.text.strip())
        b_list = data_store.bot_data.setdefault('banned_users', [])
        if user_id in b_list:
            b_list.remove(user_id)
            data_store.save_data()
            await m.reply(f"✅ تم إلغاء حظر `{user_id}`.")
        else:
            await m.reply(f"ℹ️ المستخدم `{user_id}` غير محظور أصلاً.")
    except ValueError: await m.reply("❌ ID غير صالح.")
    await state.finish()
    
async def add_channel_msg_handler(m: types.Message, state: FSMContext):
    msg_text = m.text.strip()
    data_store.bot_data.setdefault('channel_messages', []).append(msg_text)
    data_store.save_data()
    await m.reply("✅ تمت إضافة رسالة القناة بنجاح!", reply_markup=add_another_kb("add_channel_msg", "admin_channel"))
    await state.finish()

async def delete_channel_msg_handler(m: types.Message, state: FSMContext):
    try:
        idx = int(m.text.strip()) - 1
        messages = data_store.bot_data.get('channel_messages', [])
        if 0 <= idx < len(messages):
            removed = messages.pop(idx)
            data_store.save_data()
            await m.reply(f"✅ تم حذف رسالة القناة:\n`{removed}`", reply_markup=add_another_kb("delete_channel_msg", "admin_channel"))
        else: await m.reply(f"❌ رقم غير صالح. (1 - {len(messages)})")
    except (ValueError, IndexError): await m.reply("❌ إدخال خاطئ.")
    await state.finish()

async def instant_post_handler(m: types.Message, state: FSMContext):
    channel_id = data_store.bot_data.get('bot_settings', {}).get('channel_id')
    if channel_id:
        try: await m.copy_to(channel_id); await m.reply("✅ تم النشر الفوري.", reply_markup=create_admin_panel())
        except Exception as e: await m.reply(f"❌ فشل النشر: {e}")
    else: await m.reply("❌ يجب تحديد ID القناة أولاً.")
    await state.finish()
    
async def scheduled_post_content_handler(m: types.Message, state: FSMContext):
    content_type, content_value = None, None
    if m.text: content_type, content_value = "text", m.text
    elif m.sticker: content_type, content_value = "sticker", m.sticker.file_id
    elif m.photo: content_type, content_value = "photo", m.photo[-1].file_id
    else: return await m.reply("❌ نوع المحتوى هذا غير مدعوم للجدولة.")
    await state.update_data(post_content_type=content_type, post_content_value=content_value)
    tz_name = data_store.bot_data.get('ui_config', {}).get('timezone', 'Asia/Riyadh')
    await m.reply(f"👍 ممتاز. الآن أرسل وقت الإرسال (بتوقيتك المحلي: {tz_name}):\n`YYYY-MM-DD HH:MM`")
    await AdminStates.next()

async def scheduled_post_datetime_handler(m: types.Message, state: FSMContext):
    try:
        dt_str = m.text.strip()
        tz_name = data_store.bot_data.get('ui_config', {}).get('timezone', 'Asia/Riyadh')
        local_tz = pytz.timezone(tz_name)
        local_dt = local_tz.localize(datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M"))
        send_at_utc = local_dt.astimezone(pytz.utc)
        data = await state.get_data()
        content_type, content_value = data.get('post_content_type'), data.get('post_content_value')
        channel_id = data_store.bot_data.get('bot_settings', {}).get('channel_id')
        if not channel_id:
            await m.reply("❌  خطأ:  يجب تحديد ID القناة أولاً.")
            return await state.finish()
        content_id = add_content_to_library(content_type=content_type, content_value=content_value)
        add_scheduled_post(content_id=content_id, channel_id=channel_id, send_at_utc=send_at_utc)
        await m.reply(f"✅ تمت جدولة المحتوى!\nسيتم إرساله في: `{dt_str}` (بتوقيتك المحلي)", reply_markup=add_another_kb("schedule_post", "admin_channel"))
    except (ValueError, pytz.UnknownTimeZoneError) as e: await m.reply(f"❌ خطأ في التوقيت أو التنسيق! Error: {e}")
    except Exception as e: await m.reply(f"❌ حدث خطأ غير متوقع: {e}")
    await state.finish()

async def broadcast_handler(m: types.Message, state: FSMContext):
    succ, fail = 0, 0
    user_list = data_store.bot_data.get('users', [])
    if not user_list:
        await m.reply("⚠️ لا يوجد مستخدمون.", reply_markup=create_admin_panel())
        return await state.finish()
    await m.reply(f"📤 بدء الإرسال لـ {len(user_list)} مستخدم...")
    for uid in user_list:
        try: await m.copy_to(uid); succ += 1; await asyncio.sleep(0.05)
        except: fail += 1
    await m.reply(f"✅ اكتمل الإرسال:\n- نجح: {succ}\n- فشل: {fail}", reply_markup=create_admin_panel())
    await state.finish()

async def date_button_label_handler(m: types.Message, state: FSMContext):
    value = m.text.strip(); data_store.bot_data.setdefault('ui_config', {})['date_button_label'] = value; data_store.save_data()
    await m.reply(f"✅ تم تحديث اسم الزر.", reply_markup=create_admin_panel()); await state.finish()

async def time_button_label_handler(m: types.Message, state: FSMContext):
    value = m.text.strip(); data_store.bot_data.setdefault('ui_config', {})['time_button_label'] = value; data_store.save_data()
    await m.reply(f"✅ تم تحديث اسم الزر.", reply_markup=create_admin_panel()); await state.finish()

async def reminder_button_label_handler(m: types.Message, state: FSMContext):
    value = m.text.strip(); data_store.bot_data.setdefault('ui_config', {})['reminder_button_label'] = value; data_store.save_data()
    await m.reply(f"✅ تم تحديث اسم الزر.", reply_markup=create_admin_panel()); await state.finish()

async def welcome_message_handler(m: types.Message, state: FSMContext):
    value = m.html_text; data_store.bot_data.setdefault('bot_settings', {})['welcome_message'] = value; data_store.save_data()
    await m.reply(f"✅ تم تحديث رسالة البدء.", reply_markup=create_admin_panel()); await state.finish()

async def reply_message_handler(m: types.Message, state: FSMContext):
    value = m.html_text; data_store.bot_data.setdefault('bot_settings', {})['reply_message'] = value; data_store.save_data()
    await m.reply(f"✅ تم تحديث رسالة الرد.", reply_markup=create_admin_panel()); await state.finish()

async def set_timezone_handler(m: types.Message, state: FSMContext):
    tz_name_input = m.text.strip()
    tz_aliases = {"Asia/Sana'a": "Asia/Aden", "Asia/Sanaa": "Asia/Aden", "Sana'a": "Asia/Aden", "Sanaa": "Asia/Aden", "Riyadh": "Asia/Riyadh", "Aden": "Asia/Aden", "Cairo": "Africa/Cairo"}
    corrected_tz_name = tz_aliases.get(tz_name_input, tz_name_input)
    try:
        pytz.timezone(corrected_tz_name)
        data_store.bot_data.setdefault('ui_config', {})['timezone'] = corrected_tz_name; data_store.save_data()
        await m.reply(f"✅ تم تحديث المنطقة الزمنية: `{corrected_tz_name}`", reply_markup=create_admin_panel())
    except pytz.UnknownTimeZoneError: await m.reply(f"❌ **منطقة غير صالحة:** `{tz_name_input}`\nمثال: `Asia/Riyadh`")
    await state.finish()

async def set_channel_id_handler(m: types.Message, state: FSMContext):
    channel_id = m.text.strip(); data_store.bot_data.setdefault('bot_settings', {})['channel_id'] = channel_id; data_store.save_data()
    await m.reply(f"✅ تم تحديث ID القناة.", reply_markup=create_admin_panel()); await state.finish()

async def schedule_interval_handler(m: types.Message, state: FSMContext):
    try:
        hours = float(m.text.strip()); seconds = int(hours * 3600)
        if seconds < 60: await m.reply("❌ أقل فترة هي 60 ثانية.")
        else: data_store.bot_data.setdefault('bot_settings', {})['schedule_interval_seconds'] = seconds; data_store.save_data()
        await m.reply(f"✅ تم تحديث فترة النشر: {hours} ساعة.", reply_markup=create_admin_panel())
    except ValueError: await m.reply("❌ الرجاء إرسال رقم.")
    await state.finish()

async def add_media_type_handler(m: types.Message, state: FSMContext):
    media_type = m.text.strip().lower(); allowed = data_store.bot_data.setdefault('bot_settings', {}).setdefault('allowed_media_types', ['text'])
    if media_type not in allowed: allowed.append(media_type)
    data_store.save_data(); await m.reply(f"✅ تم السماح بالنوع: `{media_type}`.", reply_markup=create_admin_panel()); await state.finish()

async def remove_media_type_handler(m: types.Message, state: FSMContext):
    media_type = m.text.strip().lower(); allowed = data_store.bot_data.setdefault('bot_settings', {}).setdefault('allowed_media_types', ['text'])
    if media_type == 'text': await m.reply("❌ لا يمكن منع النص.")
    elif media_type in allowed: allowed.remove(media_type); data_store.save_data(); await m.reply(f"✅ تم منع النوع: `{media_type}`.", reply_markup=create_admin_panel())
    else: await m.reply(f"❌ النوع `{media_type}` غير مسموح به.")
    await state.finish()

async def media_reject_message_handler(m: types.Message, state: FSMContext):
    value = m.html_text; data_store.bot_data.setdefault('bot_settings', {})['media_reject_message'] = value; data_store.save_data()
    await m.reply(f"✅ تم تحديث رسالة الرفض.", reply_markup=create_admin_panel()); await state.finish()

async def spam_limit_handler(m: types.Message, state: FSMContext):
    try:
        limit = int(m.text.strip())
        if limit < 1: await m.reply("❌ الحد الأدنى 1.")
        else: data_store.bot_data.setdefault('bot_settings', {})['spam_message_limit'] = limit; data_store.save_data()
        await m.reply(f"✅ تم تحديث حد الرسائل إلى {limit}.", reply_markup=create_admin_panel())
    except ValueError: await m.reply("❌ الرجاء إرسال رقم.")
    await state.finish()

async def spam_window_handler(m: types.Message, state: FSMContext):
    try:
        window = int(m.text.strip())
        if window < 1: await m.reply("❌ الفترة الدنيا 1.")
        else: data_store.bot_data.setdefault('bot_settings', {})['spam_time_window'] = window; data_store.save_data()
        await m.reply(f"✅ تم تحديث فترة المنع إلى {window} ثانية.", reply_markup=create_admin_panel())
    except ValueError: await m.reply("❌ الرجاء إرسال رقم.")
    await state.finish()

async def slow_mode_handler(m: types.Message, state: FSMContext):
    try:
        seconds = int(m.text.strip())
        if seconds < 0: await m.reply("❌ لا يمكن أن تكون الثواني سالبة.")
        else: data_store.bot_data.setdefault('bot_settings', {})['slow_mode_seconds'] = seconds; data_store.save_data()
        await m.reply(f"✅ تم تحديث فترة التباطؤ إلى {seconds} ثانية.", reply_markup=create_admin_panel())
    except ValueError: await m.reply("❌ الرجاء إرسال رقم.")
    await state.finish()

async def clear_user_id_handler(m: types.Message, state: FSMContext):
    try:
        user_id = int(m.text.strip())
        if user_id in data_store.user_last_message_time:
            del data_store.user_last_message_time[user_id]
        await m.reply(f"✅ تم مسح ذاكرة التباطؤ للمستخدم `{user_id}`.", reply_markup=create_admin_panel())
    except ValueError: await m.reply("❌ ID غير صالح.")
    await state.finish()

# --- NEW: Handler for setting the Force Subscribe Channel ---
async def set_force_channel_id_handler(m: types.Message, state: FSMContext):
    channel_id = m.text.strip()
    if not (channel_id.startswith('@') or channel_id.startswith('-100')):
        await m.reply("❌ ID القناة غير صالح.")
        return
    data_store.bot_data.setdefault('bot_settings', {})['force_channel_id'] = channel_id
    data_store.save_data()
    await m.reply(f"✅ تم تحديد قناة الاشتراك: `{channel_id}`")
    await state.finish()
    await advanced_panel_cmd(m, state)

# --- Handler Registration ---
def register_fsm_handlers(dp: Dispatcher):
    dp.register_message_handler(cancel_cmd, is_admin, commands=['cancel'], state='*')
    
    # Register all handlers for BOTH panels
    dp.register_message_handler(dyn_reply_keyword_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_keyword)
    dp.register_message_handler(dyn_reply_content_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_dyn_reply_content)
    dp.register_message_handler(dyn_reply_delete_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_delete)
    dp.register_message_handler(import_dyn_replies_handler, is_admin, content_types=types.ContentTypes.DOCUMENT, state=AdminStates.waiting_for_dyn_replies_file)
    dp.register_message_handler(add_reminder_handler, is_admin, state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(delete_reminder_handler, is_admin, state=AdminStates.waiting_for_delete_reminder)
    dp.register_message_handler(import_reminders_handler, is_admin, content_types=types.ContentTypes.DOCUMENT, state=AdminStates.waiting_for_reminders_file)
    dp.register_message_handler(ban_user_handler, is_admin, state=AdminStates.waiting_for_ban_id)
    dp.register_message_handler(unban_user_handler, is_admin, state=AdminStates.waiting_for_unban_id)
    dp.register_message_handler(add_channel_msg_handler, is_admin, state=AdminStates.waiting_for_new_channel_msg)
    dp.register_message_handler(delete_channel_msg_handler, is_admin, state=AdminStates.waiting_for_delete_channel_msg)
    dp.register_message_handler(instant_post_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_instant_channel_post)
    dp.register_message_handler(scheduled_post_content_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_scheduled_post_content)
    dp.register_message_handler(scheduled_post_datetime_handler, is_admin, state=AdminStates.waiting_for_scheduled_post_datetime)
    dp.register_message_handler(broadcast_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_broadcast_message)
    dp.register_message_handler(date_button_label_handler, is_admin, state=AdminStates.waiting_for_date_button_label)
    dp.register_message_handler(time_button_label_handler, is_admin, state=AdminStates.waiting_for_time_button_label)
    dp.register_message_handler(reminder_button_label_handler, is_admin, state=AdminStates.waiting_for_reminder_button_label)
    dp.register_message_handler(set_timezone_handler, is_admin, state=AdminStates.waiting_for_timezone)
    dp.register_message_handler(welcome_message_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_welcome_message)
    dp.register_message_handler(reply_message_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_reply_message)
    dp.register_message_handler(set_channel_id_handler, is_admin, state=AdminStates.waiting_for_channel_id)
    dp.register_message_handler(schedule_interval_handler, is_admin, state=AdminStates.waiting_for_schedule_interval)
    dp.register_message_handler(add_media_type_handler, is_admin, state=AdminStates.waiting_for_add_media_type)
    dp.register_message_handler(remove_media_type_handler, is_admin, state=AdminStates.waiting_for_remove_media_type)
    dp.register_message_handler(media_reject_message_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_media_reject_message)
    dp.register_message_handler(spam_limit_handler, is_admin, state=AdminStates.waiting_for_spam_limit)
    dp.register_message_handler(spam_window_handler, is_admin, state=AdminStates.waiting_for_spam_window)
    dp.register_message_handler(slow_mode_handler, is_admin, state=AdminStates.waiting_for_slow_mode)
    dp.register_message_handler(clear_user_id_handler, is_admin, state=AdminStates.waiting_for_clear_user_id)
    dp.register_message_handler(set_force_channel_id_handler, is_admin, state=AdminStates.waiting_for_force_channel_id)
