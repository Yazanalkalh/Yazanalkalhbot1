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

def is_admin(message: types.Message):
    return message.from_user.id == ADMIN_CHAT_ID

# --- Main FSM Handlers ---
async def cancel_cmd(m: types.Message, state: FSMContext): 
    if await state.get_state() is not None:
        await state.finish()
        await m.reply("✅ تم إلغاء العملية بنجاح.", reply_markup=create_admin_panel())

# --- Simple Text Handlers for UI & Settings ---
async def simple_text_handler(m: types.Message, state: FSMContext, category: str, key: str, success_msg: str):
    value = m.text.strip()
    data_store.bot_data.setdefault(category, {})[key] = value
    data_store.save_data()
    await m.reply(success_msg.format(value=value), reply_markup=create_admin_panel())
    await state.finish()

# --- Handlers for Specific Logic ---
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

# --- THIS IS THE CORRECTED FUNCTION ---
async def ban_unban_user_handler(m: types.Message, state: FSMContext, ban: bool):
    try:
        user_id = int(m.text.strip())
        b_list = data_store.bot_data.setdefault('banned_users', [])
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
# ------------------------------------

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
    dp.register_message_handler(cancel_cmd, is_admin, commands=['cancel'], state='*')
    
    # Ban/Unban
    dp.register_message_handler(lambda m, s: ban_unban_user_handler(m, s, True), is_admin, state=AdminStates.waiting_for_ban_id)
    dp.register_message_handler(lambda m, s: ban_unban_user_handler(m, s, False), is_admin, state=AdminStates.waiting_for_unban_id)

    # Broadcast
    dp.register_message_handler(broadcast_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_broadcast_message)

    # Channel Posts
    dp.register_message_handler(instant_post_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_instant_channel_post)
    dp.register_message_handler(scheduled_post_text_handler, is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_scheduled_post_text)
    dp.register_message_handler(scheduled_post_datetime_handler, is_admin, state=AdminStates.waiting_for_scheduled_post_datetime)

    # UI Customization
    dp.register_message_handler(lambda m, s: simple_text_handler(m, s, 'ui_config', 'date_button_label', "✅ تم تحديث اسم الزر."), is_admin, state=AdminStates.waiting_for_date_button_label)
    dp.register_message_handler(lambda m, s: simple_text_handler(m, s, 'ui_config', 'time_button_label', "✅ تم تحديث اسم الزر."), is_admin, state=AdminStates.waiting_for_time_button_label)
    dp.register_message_handler(lambda m, s: simple_text_handler(m, s, 'ui_config', 'reminder_button_label', "✅ تم تحديث اسم الزر."), is_admin, state=AdminStates.waiting_for_reminder_button_label)
    dp.register_message_handler(set_timezone_handler, is_admin, state=AdminStates.waiting_for_timezone)
    dp.register_message_handler(lambda m, s: simple_text_handler(m, s, 'bot_settings', 'welcome_message', "✅ تم تحديث رسالة البدء."), is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_welcome_message)
    dp.register_message_handler(lambda m, s: simple_text_handler(m, s, 'bot_settings', 'reply_message', "✅ تم تحديث رسالة الرد."), is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_reply_message)
    
    # Channel Settings
    dp.register_message_handler(lambda m, s: simple_text_handler(m, s, 'bot_settings', 'channel_id', "✅ تم تحديث ID القناة."), is_admin, state=AdminStates.waiting_for_channel_id)
    dp.register_message_handler(schedule_interval_handler, is_admin, state=AdminStates.waiting_for_schedule_interval)

    # Media Settings
    dp.register_message_handler(lambda m, s: media_type_handler(m, s, True), is_admin, state=AdminStates.waiting_for_add_media_type)
    dp.register_message_handler(lambda m, s: media_type_handler(m, s, False), is_admin, state=AdminStates.waiting_for_remove_media_type)
    dp.register_message_handler(lambda m, s: simple_text_handler(m, s, 'bot_settings', 'media_reject_message', "✅ تم تحديث رسالة الرفض."), is_admin, content_types=types.ContentTypes.ANY, state=AdminStates.waiting_for_media_reject_message) 
