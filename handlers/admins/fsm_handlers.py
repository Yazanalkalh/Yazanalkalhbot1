from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
import data_store
# We now import the specific, upgraded database functions
from utils.database import add_content_to_library, add_scheduled_post
from keyboards.inline.admin_keyboards import create_admin_panel, add_another_kb
import pytz
import datetime
import asyncio

# This file contains the complete logic for all FSM states.
# The scheduling functions have been upgraded to be timezone-aware.

def is_admin(message: types.Message):
    """A filter to check if the user is an admin."""
    return message.from_user.id == ADMIN_CHAT_ID

# --- Universal Handler ---
async def cancel_cmd(m: types.Message, state: FSMContext): 
    if await state.get_state() is not None:
        await state.finish()
        await m.reply("✅ تم إلغاء العملية بنجاح.", reply_markup=create_admin_panel())

# --- Dynamic Replies Handlers (Unchanged) ---
async def dyn_reply_keyword_handler(m: types.Message, state: FSMContext):
    await state.update_data(keyword=m.text.strip())
    await m.reply("👍 الآن أرسل **المحتوى** للرد.")
    await AdminStates.next()

async def dyn_reply_content_handler(m: types.Message, state: FSMContext):
    data = await state.get_data()
    keyword = data['keyword']
    content = m.text
    data_store.bot_data.setdefault('dynamic_replies', {})[keyword] = content
    data_store.save_data()
    await m.reply("✅ **تمت برمجة الرد بنجاح!**", reply_markup=add_another_kb("add_dyn_reply", "admin_dyn_replies"))
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

# --- Reminders Handlers (Unchanged) ---
async def add_reminder_handler(m: types.Message, state: FSMContext):
    reminder_text = m.text.strip()
    data_store.bot_data.setdefault('reminders', []).append(reminder_text)
    data_store.save_data()
    await m.reply("✅ **تمت إضافة التذكير بنجاح!**", reply_markup=add_another_kb("add_reminder", "admin_reminders"))
    await state.finish()

async def delete_reminder_handler(m: types.Message, state: FSMContext):
    try:
        idx = int(m.text.strip()) - 1
        reminders = data_store.bot_data.get('reminders', [])
        if 0 <= idx < len(reminders):
            removed = reminders.pop(idx)
            data_store.save_data()
            await m.reply(f"✅ تم حذف التذكير:\n`{removed}`", reply_markup=add_another_kb("delete_reminder", "admin_reminders"))
        else:
            await m.reply(f"❌ رقم غير صالح. الرجاء إدخال رقم بين 1 و {len(reminders)}")
    except (ValueError, IndexError):
        await m.reply("❌ إدخال خاطئ. الرجاء إرسال رقم صحيح.")
    await state.finish()

# --- Ban/Unban Handlers (Unchanged) ---
async def ban_user_handler(m: types.Message, state: FSMContext):
    try:
        user_id = int(m.text.strip())
        b_list = data_store.bot_data.setdefault('banned_users', [])
        if user_id not in b_list:
            b_list.append(user_id)
            data_store.save_data()
        await m.reply(f"🚫 تم حظر `{user_id}`.", reply_markup=create_admin_panel())
    except ValueError:
        await m.reply("❌ ID غير صالح.")
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
    except ValueError:
        await m.reply("❌ ID غير صالح.")
    await state.finish()

# --- Channel Messages Handlers (Unchanged) ---
async def add_channel_msg_handler(m: types.Message, state: FSMContext):
    msg_text = m.text.strip()
    data_store.bot_data.setdefault('channel_messages', []).append(msg_text)
    data_store.save_data()
    await m.reply("✅ **تمت إضافة رسالة القناة بنجاح!**", reply_markup=add_another_kb("add_channel_msg", "admin_channel"))
    await state.finish()

async def delete_channel_msg_handler(m: types.Message, state: FSMContext):
    try:
        idx = int(m.text.strip()) - 1
        messages = data_store.bot_data.get('channel_messages', [])
        if 0 <= idx < len(messages):
            removed = messages.pop(idx)
            data_store.save_data()
            await m.reply(f"✅ تم حذف رسالة القناة:\n`{removed}`", reply_markup=add_another_kb("delete_channel_msg", "admin_channel"))
        else:
            await m.reply(f"❌ رقم غير صالح. الرجاء إدخال رقم بين 1 و {len(messages)}")
    except (ValueError, IndexError):
        await m.reply("❌ إدخال خاطئ. الرجاء إرسال رقم صحيح.")
    await state.finish()

async def instant_post_handler(m: types.Message, state: FSMContext):
    channel_id = data_store.bot_data.get('bot_settings', {}).get('channel_id')
    if channel_id:
        try:
            await m.copy_to(channel_id)
            await m.reply("✅ تم النشر الفوري بنجاح.", reply_markup=create_admin_panel())
        except Exception as e:
            await m.reply(f"❌ فشل النشر: {e}")
    else:
        await m.reply("❌ يجب تحديد ID القناة أولاً.")
    await state.finish()

# --- UPGRADED: Scheduled Post Handlers ---

async def scheduled_post_content_handler(m: types.Message, state: FSMContext):
    """
    UPGRADED: This function now understands multiple content types and asks for LOCAL time.
    """
    content_type = None
    content_value = None

    if m.text:
        content_type = "text"
        content_value = m.text
    elif m.sticker:
        content_type = "sticker"
        content_value = m.sticker.file_id
    elif m.photo:
        content_type = "photo"
        content_value = m.photo[-1].file_id
    else:
        await m.reply("❌ نوع المحتوى هذا غير مدعوم للجدولة حاليًا. الرجاء إرسال نص، ملصق، أو صورة.")
        return

    await state.update_data(
        post_content_type=content_type,
        post_content_value=content_value
    )
    
    # Get the admin's timezone to display in the prompt message
    tz_name = data_store.bot_data.get('ui_config', {}).get('timezone', 'Asia/Riyadh') # Fallback to Riyadh
    await m.reply(f"👍 ممتاز. الآن أرسل وقت الإرسال بالتنسيق التالي (بتوقيتك المحلي: {tz_name}):\n`YYYY-MM-DD HH:MM`\nمثال: `2025-12-31 23:59`")
    await AdminStates.next()

async def scheduled_post_datetime_handler(m: types.Message, state: FSMContext):
    """
    UPGRADED: This function now acts as a "Smart Assistant".
    It understands local time, converts it to UTC, and then schedules the post.
    """
    try:
        dt_str = m.text.strip()
        
        # 1. Get the admin's local timezone from settings
        try:
            tz_name = data_store.bot_data.get('ui_config', {}).get('timezone', 'Asia/Riyadh')
            local_tz = pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            await m.reply(f"⚠️ المنطقة الزمنية '{tz_name}' غير صالحة. سيتم استخدام UTC كافتراضي.")
            local_tz = pytz.utc

        # 2. Convert the "naive" local time string from the admin to a "timezone-aware" datetime object
        local_dt = local_tz.localize(datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M"))
        
        # 3. Translate the local datetime object to the universal UTC time for storage
        send_at_utc = local_dt.astimezone(pytz.utc)
        
        data = await state.get_data()
        content_type = data.get('post_content_type')
        content_value = data.get('post_content_value')

        channel_id = data_store.bot_data.get('bot_settings', {}).get('channel_id')
        if not channel_id:
            await m.reply("❌ **خطأ:** يجب تحديد ID القناة أولاً قبل جدولة المنشورات.")
            await state.finish()
            return

        # 4. Add content to the library (if not exists) and get its reference ID
        content_id = add_content_to_library(content_type=content_type, content_value=content_value)

        # 5. Schedule the post using the content ID and the translated UTC time
        add_scheduled_post(content_id=content_id, channel_id=channel_id, send_at_utc=send_at_utc)

        await m.reply(f"✅ **تمت جدولة المحتوى بنجاح!**\nسيتم إرساله في: `{dt_str}` (بتوقيتك المحلي)", reply_markup=add_another_kb("schedule_post", "admin_channel"))
    
    except ValueError:
        await m.reply("❌ **تنسيق التاريخ خاطئ!** الرجاء استخدام `YYYY-MM-DD HH:MM`.")
    except Exception as e:
        await m.reply(f"❌ حدث خطأ غير متوقع: {e}")
    
    await state.finish()

# --- Other Handlers (Broadcast, UI, etc. are unchanged) ---
async def broadcast_handler(m: types.Message, state: FSMContext):
    succ, fail = 0, 0
    user_list = data_store.bot_data.get('users', [])
    if not user_list:
        await m.reply("⚠️ لا يوجد مستخدمون لإرسال الرسالة إليهم.", reply_markup=create_admin_panel())
        await state.finish()
        return
    await m.reply(f"📤 بدء الإرسال لـ {len(user_list)} مستخدم... قد يستغرق هذا بعض الوقت.")
    for uid in user_list:
        try:
            await m.copy_to(uid)
            succ += 1
            await asyncio.sleep(0.05)
        except:
            fail += 1
    await m.reply(f"✅ **اكتمل الإرسال:**\n\n- نجح: {succ}\n- فشل: {fail}", reply_markup=create_admin_panel())
    await state.finish()

async def date_button_label_handler(m: types.Message, state: FSMContext):
    value = m.text.strip()
    data_store.bot_data.setdefault('ui_config', {})['date_button_label'] = value
    data_store.save_data()
    await m.reply(f"✅ تم تحديث اسم زر التاريخ إلى: `{value}`", reply_markup=create_admin_panel())
    await state.finish()

async def time_button_label_handler(m: types.Message, state: FSMContext):
    value = m.text.strip()
    data_store.bot_data.setdefault('ui_config', {})['time_button_label'] = value
    data_store.save_data()
    await m.reply(f"✅ تم تحديث اسم زر الساعة إلى: `{value}`", reply_markup=create_admin_panel())
    await state.finish()

async def reminder_button_label_handler(m: types.Message, state: FSMContext):
    value = m.text.strip()
    data_store.bot_data.setdefault('ui_config', {})['reminder_button_label'] = value
    data_store.save_data()
    await m.reply(f"✅ تم تحديث اسم زر التذكير إلى: `{value}`", reply_markup=create_admin_panel())
    await state.finish()

async def welcome_message_handler(m: types.Message, state: FSMContext):
    value = m.text
    data_store.bot_data.setdefault('bot_settings', {})['welcome_message'] = value
    data_store.save_data()
    await m.reply(f"✅ تم تحديث رسالة البدء بنجاح.", reply_markup=create_admin_panel())
    await state.finish()

async def reply_message_handler(m: types.Message, state: FSMContext):
    value = m.text
    data_store.bot_data.setdefault('bot_settings', {})['reply_message'] = value
    data_store.save_data()
    await m.reply(f"✅ تم تحديث رسالة الرد بنجاح.", reply_markup=create_admin_panel())
    await state.finish()

async def set_timezone_handler(m: types.Message, state: FSMContext):
    tz_name = m.text.strip()
    try:
        pytz.timezone(tz_name)
        data_store.bot_data.setdefault('ui_config', {})['timezone'] = tz_name
        data_store.save_data()
        await m.reply(f"✅ تم تحديث المنطقة الزمنية إلى: `{tz_name}`", reply_markup=create_admin_panel())
    except pytz.UnknownTimeZoneError:
        await m.reply("❌ **منطقة زمنية غير صالحة!**\nمثال: `Asia/Riyadh`")
    await state.finish()

async def set_channel_id_handler(m: types.Message, state: FSMContext):
    channel_id = m.text.strip()
    data_store.bot_data.setdefault('bot_settings', {})['channel_id'] = channel_id
    data_store.save_data()
    await m.reply(f"✅ تم تحديث ID القناة إلى: `{channel_id}`", reply_markup=create_admin_panel())
    await state.finish()

async def schedule_interval_handler(m: types.Message, state: FSMContext):
    try:
        hours = float(m.text.strip())
        seconds = int(hours * 3600)
        if seconds < 60:
            await m.reply("❌ أقل فترة مسموحة هي 60 ثانية.")
        else:
            data_store.bot_data.setdefault('bot_settings', {})['schedule_interval_seconds'] = seconds
            data_store.save_data()
            await m.reply(f"✅ تم تحديث فترة النشر التلقائي إلى كل {hours} ساعة.", reply_markup=create_admin_panel())
    except ValueError:
        await m.reply("❌ الرجاء إرسال رقم صحيح.")
    await state.finish()

async def add_media_type_handler(m: types.Message, state: FSMContext):
    media_type = m.text.strip().lower()
    allowed = data_store.bot_data.setdefault('bot_settings', {}).setdefault('allowed_media_types', ['text'])
    if media_type not in allowed:
        allowed.append(media_type)
    data_store.save_data()
    await m.reply(f"✅ تم السماح بالنوع: `{media_type}`.", reply_markup=create_admin_panel())
    await state.finish()

async def remove_media_type_handler(m: types.Message, state: FSMContext):
    media_type = m.text.strip().lower()
    allowed = data_store.bot_data.setdefault('bot_settings', {}).setdefault('allowed_media_types', ['text'])
    if media_type == 'text':
        await m.reply("❌ لا يمكن منع الرسائل النصية.")
    elif media_type in allowed:
        allowed.remove(media_type)
        data_store.save_data()
        await m.reply(f"✅ تم منع النوع: `{media_type}`.", reply_markup=create_admin_panel())
    else:
        await m.reply(f"❌ النوع `{media_type}` غير مسموح به أصلاً.")
    await state.finish()

async def media_reject_message_handler(m: types.Message, state: FSMContext):
    value = m.text
    data_store.bot_data.setdefault('bot_settings', {})['media_reject_message'] = value
    data_store.save_data()
    await m.reply(f"✅ تم تحديث رسالة الرفض بنجاح.", reply_markup=create_admin_panel())
    await state.finish()

# --- Handler Registration ---
def register_fsm_handlers(dp: Dispatcher):
    """Registers all the FSM handlers."""
    dp.register_message_handler(cancel_cmd, is_admin, commands=['cancel'], state='*')
    
    # Dynamic Replies (Unchanged)
    dp.register_message_handler(dyn_reply_keyword_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_keyword)
    dp.register_message_handler(dyn_reply_content_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_dyn_reply_content)
    dp.register_message_handler(dyn_reply_delete_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_delete)

    # Reminders (Unchanged)
    dp.register_message_handler(add_reminder_handler, is_admin, state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(delete_reminder_handler, is_admin, state=AdminStates.waiting_for_delete_reminder)

    # Ban/Unban (Unchanged)
    dp.register_message_handler(ban_user_handler, is_admin, state=AdminStates.waiting_for_ban_id)
    dp.register_message_handler(unban_user_handler, is_admin, state=AdminStates.waiting_for_unban_id)

    # Channel Messages (Unchanged)
    dp.register_message_handler(add_channel_msg_handler, is_admin, state=AdminStates.waiting_for_new_channel_msg)
    dp.register_message_handler(delete_channel_msg_handler, is_admin, state=AdminStates.waiting_for_delete_channel_msg)
    dp.register_message_handler(instant_post_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_instant_channel_post)
    
    # UPGRADED: Scheduled Post Handlers Registration
    dp.register_message_handler(scheduled_post_content_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_scheduled_post_text)
    dp.register_message_handler(scheduled_post_datetime_handler, is_admin, state=AdminStates.waiting_for_scheduled_post_datetime)

    # Broadcast (Unchanged)
    dp.register_message_handler(broadcast_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_broadcast_message)
    
    # UI Customization (Unchanged)
    dp.register_message_handler(date_button_label_handler, is_admin, state=AdminStates.waiting_for_date_button_label)
    dp.register_message_handler(time_button_label_handler, is_admin, state=AdminStates.waiting_for_time_button_label)
    dp.register_message_handler(reminder_button_label_handler, is_admin, state=AdminStates.waiting_for_reminder_button_label)
    dp.register_message_handler(set_timezone_handler, is_admin, state=AdminStates.waiting_for_timezone)
    dp.register_message_handler(welcome_message_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_welcome_message)
    dp.register_message_handler(reply_message_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_reply_message)
    
    # Channel Settings (Unchanged)
    dp.register_message_handler(set_channel_id_handler, is_admin, state=AdminStates.waiting_for_channel_id)
    dp.register_message_handler(schedule_interval_handler, is_admin, state=AdminStates.waiting_for_schedule_interval)

    # Media Settings (Unchanged)
    dp.register_message_handler(add_media_type_handler, is_admin, state=AdminStates.waiting_for_add_media_type)
    dp.register_message_handler(remove_media_type_handler, is_admin, state=AdminStates.waiting_for_remove_media_type)
    dp.register_message_handler(media_reject_message_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_media_reject_message)
