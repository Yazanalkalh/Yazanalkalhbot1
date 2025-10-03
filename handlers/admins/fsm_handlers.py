import asyncio
import datetime
import pytz
from aiogram import types
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
import data_store
from keyboards.inline.admin_keyboards import create_admin_panel, add_another_kb

# --- FSM Handlers ---

async def cancel_cmd(m: types.Message, state: FSMContext):
    await state.finish()
    await m.reply("✅ تم إلغاء العملية.", reply_markup=create_admin_panel())

async def process_text_input(m: types.Message, state: FSMContext, data_key: list, success_msg: str, is_list=False, kb_info=None):
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
    await state.finish()

async def process_numeric_input(m: types.Message, state: FSMContext, data_key: list, success_msg: str):
    try:
        val = int(m.text.strip())
        target = data_store.bot_data
        for k in data_key[:-1]:
            target = target.setdefault(k, {})
        target[data_key[-1]] = val
        data_store.save_data()
        await m.reply(success_msg.format(value=val), reply_markup=create_admin_panel())
    except ValueError:
        await m.reply("❌ الرجاء إرسال رقم صحيح.")
    await state.finish()

async def process_delete_by_index(m: types.Message, state: FSMContext, data_key: str, item_name: str, kb_info: tuple):
    try:
        idx = int(m.text.strip()) - 1
        lst = data_store.bot_data.get(data_key, [])
        if 0 <= idx < len(lst):
            removed = lst.pop(idx)
            data_store.save_data()
            await m.reply(f"✅ تم حذف {item_name}:\n`{removed}`", reply_markup=add_another_kb(*kb_info))
        else:
            await m.reply(f"❌ رقم غير صالح. (1 - {len(lst)})")
    except (ValueError, IndexError):
        await m.reply("❌ الرجاء إرسال رقم صحيح.")
    await state.finish()

async def dyn_reply_keyword(m: types.Message, state: FSMContext):
    await state.update_data(keyword=m.text.strip())
    await m.reply("👍 الآن أرسل **المحتوى**.")
    await AdminStates.next()

async def dyn_reply_content(m: types.Message, state: FSMContext):
    data = await state.get_data()
    keyword, content = data['keyword'], m.text
    data_store.bot_data['dynamic_replies'][keyword] = content
    data_store.save_data()
    await m.reply("✅ **تمت برمجة الرد!**", reply_markup=add_another_kb("add_dyn_reply", "admin_dyn_replies"))
    await state.finish()

async def dyn_reply_delete(m: types.Message, state: FSMContext):
    keyword = m.text.strip()
    if keyword in data_store.bot_data['dynamic_replies']:
        del data_store.bot_data['dynamic_replies'][keyword]
        data_store.save_data()
        await m.reply(f"✅ تم حذف الرد الخاص بـ `{keyword}`", reply_markup=add_another_kb("delete_dyn_reply", "admin_dyn_replies"))
    else:
        await m.reply("❌ لم يتم العثور على رد.", reply_markup=create_admin_panel())
    await state.finish()

async def scheduled_post_text(m: types.Message, state: FSMContext):
    await state.update_data(post_text=m.text.strip())
    await m.reply("👍 الآن أرسل وقت الإرسال:\n`YYYY-MM-DD HH:MM` (بتوقيت UTC)")
    await AdminStates.next()

async def scheduled_post_datetime(m: types.Message, state: FSMContext):
    try:
        dt_str = m.text.strip()
        send_at_utc = pytz.utc.localize(datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M"))
        data = await state.get_data()
        post_text = data['post_text']
        channel_id = data_store.bot_data['bot_settings']['channel_id']
        
        if not channel_id:
            await m.reply("❌ **خطأ:** يجب تحديد ID القناة أولاً.")
            await state.finish()
            return
        
        new_post = {"text": post_text, "channel_id": channel_id, "send_at_iso": send_at_utc.isoformat()}
        data_store.bot_data.setdefault("scheduled_posts", []).append(new_post)
        data_store.save_data()
        await m.reply("✅ **تمت جدولة الرسالة!**", reply_markup=add_another_kb("schedule_post", "admin_channel"))
    except ValueError:
        await m.reply("❌ **تنسيق التاريخ خاطئ!**")
    await state.finish()

async def ban_unban_user(m: types.Message, state: FSMContext, ban: bool):
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
    await state.finish()

async def broadcast_msg(m: types.Message, state: FSMContext):
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
    await state.finish()

async def clear_user(m: types.Message, state: FSMContext):
    try:
        uid = int(m.text.strip())
        c = 0
        if uid in data_store.user_last_message_time:
            del data_store.user_last_message_time[uid]
            c += 1
        await m.reply(f"✅ تم مسح {c} سجل حماية للمستخدم `{uid}`.", reply_markup=create_admin_panel())
    except ValueError:
        await m.reply("❌ ID غير صالح.")
    await state.finish()

async def set_timezone(m: types.Message, state: FSMContext):
    try:
        tz = m.text.strip()
        pytz.timezone(tz)
        data_store.bot_data['ui_config']['timezone'] = tz
        data_store.save_data()
        await m.reply(f"✅ تم تحديث المنطقة الزمنية إلى: `{tz}`", reply_markup=create_admin_panel())
    except pytz.UnknownTimeZoneError:
        await m.reply("❌ **منطقة زمنية غير صالحة!**\nمثال: `Asia/Aden`")
    await state.finish()

async def remove_media_type(m: types.Message, state: FSMContext):
    media_type = m.text.strip()
    allowed = data_store.bot_data['bot_settings']['allowed_media_types']
    if media_type in allowed and media_type != 'text':
        allowed.remove(media_type)
        data_store.save_data()
        await m.reply(f"✅ تم منع النوع: `{media_type}`", reply_markup=create_admin_panel())
    elif media_type == 'text':
        await m.reply("❌ لا يمكن منع الرسائل النصية.")
    else:
        await m.reply(f"❌ النوع `{media_type}` غير مسموح به أصلاً.")
    await state.finish()

async def instant_post_handler(m: types.Message, state: FSMContext):
    channel_id = data_store.bot_data['bot_settings'].get('channel_id')
    if channel_id:
        try:
            await bot.send_message(channel_id, m.text.strip())
            await m.reply("✅ تم النشر الفوري بنجاح.", reply_markup=create_admin_panel())
        except Exception as e:
            await m.reply(f"❌ فشل النشر: {e}")
    else:
        await m.reply("❌ يجب تحديد ID القناة أولاً.")
    await state.finish()

async def schedule_interval_handler(m: types.Message, state: FSMContext):
    try:
        hours = float(m.text.strip())
        seconds = int(hours * 3600)
        if seconds < 60:
            await m.reply("❌ أقل فترة هي 60 ثانية.")
        else:
            data_store.bot_data['bot_settings']['schedule_interval_seconds'] = seconds
            data_store.save_data()
            await m.reply(f"✅ تم تحديث فترة النشر إلى كل {hours} ساعة.", reply_markup=create_admin_panel())
    except ValueError:
        await m.reply("❌ الرجاء إرسال رقم صحيح.")
    await state.finish()

# --- Handler Registration ---
def register_fsm_handlers(dp: types.Dispatcher):
    # This function registers all the state handlers.
    dp.register_message_handler(cancel_cmd, commands=['cancel'], state='*')

    # Dynamic Replies
    dp.register_message_handler(dyn_reply_keyword, state=AdminStates.waiting_for_dyn_reply_keyword)
    dp.register_message_handler(dyn_reply_content, state=AdminStates.waiting_for_dyn_reply_content)
    dp.register_message_handler(dyn_reply_delete, state=AdminStates.waiting_for_dyn_reply_delete)

    # Reminders
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['reminders'], "✅ تم إضافة التذكير.", True, ("add_reminder", "admin_reminders")), state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(lambda m, s: process_delete_by_index(m, s, "reminders", "التذكير", ("delete_reminder", "admin_reminders")), state=AdminStates.waiting_for_delete_reminder)

    # Channel Messages
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['channel_messages'], "✅ تم إضافة رسالة القناة.", True, ("add_channel_msg", "admin_channel")), state=AdminStates.waiting_for_new_channel_msg)
    dp.register_message_handler(lambda m, s: process_delete_by_index(m, s, "channel_messages", "الرسالة", ("delete_channel_msg", "admin_channel")), state=AdminStates.waiting_for_delete_channel_msg)
    dp.register_message_handler(instant_post_handler, state=AdminStates.waiting_for_instant_channel_post)

    # Scheduled Posts
    dp.register_message_handler(scheduled_post_text, state=AdminStates.waiting_for_scheduled_post_text)
    dp.register_message_handler(scheduled_post_datetime, state=AdminStates.waiting_for_scheduled_post_datetime)

    # Ban Management
    dp.register_message_handler(lambda m, s: ban_unban_user(m, s, True), state=AdminStates.waiting_for_ban_id)
    dp.register_message_handler(lambda m, s: ban_unban_user(m, s, False), state=AdminStates.waiting_for_unban_id)

    # Broadcast
    dp.register_message_handler(broadcast_msg, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_broadcast_message)

    # UI Customization
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['ui_config', 'date_button_label'], "✅ تم تحديث اسم الزر."), state=AdminStates.waiting_for_date_button_label)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['ui_config', 'time_button_label'], "✅ تم تحديث اسم الزر."), state=AdminStates.waiting_for_time_button_label)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['ui_config', 'reminder_button_label'], "✅ تم تحديث اسم الزر."), state=AdminStates.waiting_for_reminder_button_label)
    dp.register_message_handler(set_timezone, state=AdminStates.waiting_for_timezone)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['bot_settings', 'welcome_message'], "✅ تم تحديث رسالة الترحيب."), state=AdminStates.waiting_for_welcome_message)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['bot_settings', 'reply_message'], "✅ تم تحديث رسالة الرد."), state=AdminStates.waiting_for_reply_message)

    # Memory Management
    dp.register_message_handler(clear_user, state=AdminStates.waiting_for_clear_user_id)

    # Channel Settings
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['bot_settings', 'channel_id'], "✅ تم تحديث ID القناة."), state=AdminStates.waiting_for_channel_id)
    dp.register_message_handler(schedule_interval_handler, state=AdminStates.waiting_for_schedule_interval)

    # Security Settings
    dp.register_message_handler(lambda m, s: process_numeric_input(m, s, ['bot_settings', 'spam_message_limit'], "✅ تم تحديث حد الرسائل."), state=AdminStates.waiting_for_spam_limit)
    dp.register_message_handler(lambda m, s: process_numeric_input(m, s, ['bot_settings', 'spam_time_window'], "✅ تم تحديث الفترة الزمنية."), state=AdminStates.waiting_for_spam_window)
    dp.register_message_handler(lambda m, s: process_numeric_input(m, s, ['bot_settings', 'slow_mode_seconds'], "✅ تم تحديث فترة التباطؤ."), state=AdminStates.waiting_for_slow_mode)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['bot_settings', 'allowed_media_types'], "✅ تم السماح بالنوع: {value}", True), state=AdminStates.waiting_for_add_media_type)
    dp.register_message_handler(remove_media_type, state=AdminStates.waiting_for_remove_media_type)
    dp.register_message_handler(lambda m, s: process_text_input(m, s, ['bot_settings', 'media_reject_message'], "✅ تم تحديث رسالة الرفض."), state=AdminStates.waiting_for_media_reject_message) 
