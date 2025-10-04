from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from loader import bot
from states.admin_states import AdminStates
from config import ADMIN_CHAT_ID
import data_store
from keyboards.inline.admin_keyboards import create_admin_panel, add_another_kb
import pytz
import datetime
import asyncio

# This file contains all the logic for handling messages once the bot is in a "waiting state" (FSM).
# Each function here corresponds to a specific state defined in states/admin_states.py.

def is_admin(message: types.Message):
    """A filter to check if the user is an admin."""
    return message.from_user.id == ADMIN_CHAT_ID

# --- Universal Handlers ---
async def cancel_cmd(m: types.Message, state: FSMContext): 
    """Universal cancel handler to exit any state."""
    if await state.get_state() is not None:
        await state.finish()
        await m.reply("✅ تم إلغاء العملية بنجاح.", reply_markup=create_admin_panel())

# --- Dynamic Replies Handlers ---
async def dyn_reply_keyword_handler(m: types.Message, state: FSMContext):
    await state.update_data(keyword=m.text.strip())
    await m.reply("👍 الآن أرسل **المحتوى** للرد (يمكن أن يكون نصًا، صورة، الخ).")
    await AdminStates.next()

async def dyn_reply_content_handler(m: types.Message, state: FSMContext):
    data = await state.get_data()
    keyword = data['keyword']
    # Storing message content in a serializable format is complex.
    # For now, we'll just store the text. Advanced handling can be added later.
    content = m.text 
    if not content:
        await m.reply("❌ المحتوى لا يمكن أن يكون فارغًا. الرجاء إرسال نص.")
        return
        
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

# --- Reminders Handlers ---
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

# --- Ban/Unban Handlers ---
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

# --- Channel Messages Handlers ---
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
    
async def scheduled_post_text_handler(m: types.Message, state: FSMContext):
    await state.update_data(post_text=m.text)
    await m.reply("👍 ممتاز. الآن أرسل وقت الإرسال بالتنسيق التالي (بتوقيت UTC):\n`YYYY-MM-DD HH:MM`\nمثال: `2025-12-31 23:59`")
    await AdminStates.next()

async def scheduled_post_datetime_handler(m: types.Message, state: FSMContext):
    try:
        dt_str = m.text.strip()
        send_at_utc = pytz.utc.localize(datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M"))
        data = await state.get_data()
        post_text = data['post_text']
        channel_id = data_store.bot_data.get('bot_settings', {}).get('channel_id')

        if not channel_id:
            await m.reply("❌ **خطأ:** يجب تحديد ID القناة أولاً قبل جدولة المنشورات.")
            await state.finish()
            return

        new_post = {"text": post_text, "channel_id": channel_id, "send_at_iso": send_at_utc.isoformat()}
        data_store.bot_data.setdefault("scheduled_posts", []).append(new_post)
        data_store.save_data()
        await m.reply(f"✅ **تمت جدولة الرسالة بنجاح!**\nسيتم إرسالها في: `{dt_str}` UTC", reply_markup=add_another_kb("schedule_post", "admin_channel"))
    except ValueError:
        await m.reply("❌ **تنسيق التاريخ خاطئ!** الرجاء المحاولة مرة أخرى.")
    await state.finish()

# --- Broadcast Handler ---
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
        except Exception:
            fail += 1
    await m.reply(f"✅ **اكتمل الإرسال:**\n\n- نجح: {succ}\n- فشل: {fail}", reply_markup=create_admin_panel())
    await state.finish()

# --- UI Customization Handlers ---
async def simple_ui_text_handler(m: types.Message, state: FSMContext, key: str, success_msg: str):
    value = m.text.strip()
    data_store.bot_data.setdefault('ui_config', {})[key] = value
    data_store.save_data()
    await m.reply(success_msg.format(value=value), reply_markup=create_admin_panel())
    await state.finish()

async def simple_settings_text_handler(m: types.Message, state: FSMContext, key: str, success_msg: str):
    value = m.text.strip()
    data_store.bot_data.setdefault('bot_settings', {})[key] = value
    data_store.save_data()
    await m.reply(success_msg.format(value=value), reply_markup=create_admin_panel())
    await state.finish()

async def set_timezone_handler(m: types.Message, state: FSMContext):
    tz_name = m.text.strip()
    try:
        pytz.timezone(tz_name)
        data_store.bot_data.setdefault('ui_config', {})['timezone'] = tz_name
        data_store.save_data()
        await m.reply(f"✅ تم تحديث المنطقة الزمنية إلى: `{tz_name}`", reply_markup=create_admin_panel())
    except pytz.UnknownTimeZoneError:
        await m.reply("❌ **منطقة زمنية غير صالحة!**\nمثال: `Asia/Aden` أو `Africa/Cairo`")
    await state.finish()

# --- Channel Settings Handlers ---
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
            await m.reply("❌ أقل فترة مسموحة هي 60 ثانية (0.016 ساعة).")
        else:
            data_store.bot_data.setdefault('bot_settings', {})['schedule_interval_seconds'] = seconds
            data_store.save_data()
            await m.reply(f"✅ تم تحديث فترة النشر التلقائي إلى كل {hours} ساعة.", reply_markup=create_admin_panel())
    except ValueError:
        await m.reply("❌ الرجاء إرسال رقم صحيح (مثال: 12 أو 0.5).")
    await state.finish()

# --- Media Settings Handlers ---
async def media_type_handler(m: types.Message, state: FSMContext, add: bool):
    media_type = m.text.strip().lower()
    allowed = data_store.bot_data.setdefault('bot_settings', {}).setdefault('allowed_media_types', ['text'])
    if add:
        if media_type not in allowed: allowed.append(media_type)
        await m.reply(f"✅ تم السماح بالنوع: `{media_type}`.", reply_markup=create_admin_panel())
    else:
        if media_type == 'text':
            await m.reply("❌ لا يمكن منع الرسائل النصية.")
        elif media_type in allowed:
            allowed.remove(media_type)
            await m.reply(f"✅ تم منع النوع: `{media_type}`.", reply_markup=create_admin_panel())
        else:
            await m.reply(f"❌ النوع `{media_type}` غير مسموح به أصلاً.")
    data_store.save_data()
    await state.finish()

# --- Handler Registration ---
def register_fsm_handlers(dp: Dispatcher):
    """Registers all the FSM handlers."""
    # Universal cancel command
    dp.register_message_handler(cancel_cmd, is_admin, commands=['cancel'], state='*')
    
    # Dynamic Replies
    dp.register_message_handler(dyn_reply_keyword_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_keyword)
    dp.register_message_handler(dyn_reply_content_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_dyn_reply_content)
    dp.register_message_handler(dyn_reply_delete_handler, is_admin, state=AdminStates.waiting_for_dyn_reply_delete)

    # Reminders
    dp.register_message_handler(add_reminder_handler, is_admin, state=AdminStates.waiting_for_new_reminder)
    dp.register_message_handler(delete_reminder_handler, is_admin, state=AdminStates.waiting_for_delete_reminder)

    # Ban/Unban
    dp.register_message_handler(ban_user_handler, is_admin, state=AdminStates.waiting_for_ban_id)
    dp.register_message_handler(unban_user_handler, is_admin, state=AdminStates.waiting_for_unban_id)

    # Channel Messages
    dp.register_message_handler(add_channel_msg_handler, is_admin, state=AdminStates.waiting_for_new_channel_msg)
    dp.register_message_handler(delete_channel_msg_handler, is_admin, state=AdminStates.waiting_for_delete_channel_msg)
    dp.register_message_handler(instant_post_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_instant_channel_post)
    dp.register_message_handler(scheduled_post_text_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_scheduled_post_text)
    dp.register_message_handler(scheduled_post_datetime_handler, is_admin, state=AdminStates.waiting_for_scheduled_post_datetime)

    # Broadcast
    dp.register_message_handler(broadcast_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_broadcast_message)

    # --- THIS IS THE FINAL FIX ---
    # The lambda functions are now correctly defined to accept both 'm' (message) and 's' (state)
    
    # UI Customization
    dp.register_message_handler(lambda m, s: simple_ui_text_handler(m, s, 'date_button_label', "✅ تم تحديث اسم الزر."), is_admin, state=AdminStates.waiting_for_date_button_label)
    dp.register_message_handler(lambda m, s: simple_ui_text_handler(m, s, 'time_button_label', "✅ تم تحديث اسم الزر."), is_admin, state=AdminStates.waiting_for_time_button_label)
    dp.register_message_handler(lambda m, s: simple_ui_text_handler(m, s, 'reminder_button_label', "✅ تم تحديث اسم الزر."), is_admin, state=AdminStates.waiting_for_reminder_button_label)
    dp.register_message_handler(set_timezone_handler, is_admin, state=AdminStates.waiting_for_timezone)
    dp.register_message_handler(lambda m, s: simple_settings_text_handler(m, s, 'welcome_message', "✅ تم تحديث رسالة البدء."), is_admin, state=AdminStates.waiting_for_welcome_message)
    dp.register_message_handler(lambda m, s: simple_settings_text_handler(m, s, 'reply_message', "✅ تم تحديث رسالة الرد."), is_admin, state=AdminStates.waiting_for_reply_message)
    
    # Channel Settings
    dp.register_message_handler(set_channel_id_handler, is_admin, state=AdminStates.waiting_for_channel_id)
    dp.register_message_handler(schedule_interval_handler, is_admin, state=AdminStates.waiting_for_schedule_interval)

    # Media Settings
    dp.register_message_handler(lambda m, s: media_type_handler(m, s, True), is_admin, state=AdminStates.waiting_for_add_media_type)
    dp.register_message_handler(lambda m, s: media_type_handler(m, s, False), is_admin, state=AdminStates.waiting_for_remove_media_type)
    dp.register_message_handler(lambda m, s: simple_settings_text_handler(m, s, 'media_reject_message', "✅ تم تحديث رسالة الرفض."), is_admin, state=AdminStates.waiting_for_media_reject_message)
