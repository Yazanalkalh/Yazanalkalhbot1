from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from utils import database, texts
from keyboards.inline.advanced_keyboards import create_advanced_panel, get_advanced_submenu
from states.admin_states import AdminStates

def is_admin(message: types.Message):
    return message.from_user.id == database.ADMIN_CHAT_ID

async def advanced_panel_cmd(m: types.Message, state: FSMContext):
    if await state.get_state() is not None: await state.finish()
    await m.reply(await texts.get_text("adv_panel_title"), reply_markup=await create_advanced_panel())

async def advanced_callbacks_cmd(cq: types.CallbackQuery, state: FSMContext):
    await cq.answer()
    d = cq.data
    
    if d == "back_to_advanced":
        await cq.message.edit_text(await texts.get_text("adv_panel_title"), reply_markup=await create_advanced_panel())
        return

    toggle_map = {
        "adv_toggle_maintenance": "maintenance_mode",
        "adv_toggle_antispam": "anti_duplicate_mode",
        "adv_toggle_force_sub": "force_subscribe",
        "adv_toggle_success_notify": "notification_on_success",
        "adv_toggle_fail_notify": "notification_on_fail",
    }
    if d in toggle_map:
        key = toggle_map[d]
        current_status = await database.get_setting(key, False)
        await database.update_setting(key, not current_status)
        
        is_notification_toggle = 'notify' in d
        markup = await get_advanced_submenu("adv_notifications") if is_notification_toggle else await create_advanced_panel()
        await cq.message.edit_reply_markup(markup)
        
        status_text = "تفعيل" if not current_status else "تعطيل"
        feature_name = d.replace("adv_toggle_", "").replace("_", " ")
        await cq.answer(await texts.get_text("adv_toggle_success", status=status_text, feature_name=feature_name))
        return

    sub_menus = ["adv_notifications", "adv_manage_library", "adv_manage_channels", "adv_stats"]
    if d in sub_menus:
        await cq.message.edit_text("...", reply_markup=await get_advanced_submenu(d))
        return

    if d == "adv_system_status":
        stats = await database.get_db_stats()
        text = (f"🔬 **مراقبة حالة النظام**\n\n"
                f"▫️ **DB:** {'متصلة ✅' if stats.get('ok') else '❌'}\n"
                f"▫️ **المحتوى:** {stats.get('library_count', 0)} عنصر\n"
                f"▫️ **المجدول:** {stats.get('scheduled_count', 0)} منشور\n"
                f"▫️ **المستخدمون:** {stats.get('users_count', 0)} مستخدم")
        back_button = types.InlineKeyboardButton(await texts.get_text("back_to_advanced_panel"), callback_data="back_to_advanced")
        await cq.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup().add(back_button))
        return
        
    if d == "adv_view_library":
        content_list = await database.get_all_library_content(20)
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        text = "📚 **محتويات المكتبة (آخر 20):**\nاضغط على عنصر لحذفه."
        if not content_list:
            text = "📚 **مكتبة المحتوى فارغة حاليًا.**"
        else:
            for item in content_list:
                snippet = item.get('value', '')[:40].replace('\n', ' ') + "..."
                keyboard.add(types.InlineKeyboardButton(f"🗑️ `{item.get('type')}`: {snippet}", callback_data=f"adv_delete_lib_id_{item['_id']}"))
        keyboard.add(types.InlineKeyboardButton("🔙 العودة", callback_data="adv_manage_library"))
        await cq.message.edit_text(text, reply_markup=keyboard)
        return

    if d.startswith("adv_delete_lib_id_"):
        item_id = d.replace("adv_delete_lib_id_", "")
        await database.delete_content_by_id(item_id)
        await cq.answer("✅ تم الحذف.", show_alert=True)
        cq.data = "adv_view_library"
        await advanced_callbacks_cmd(cq, state)
        return
        
    if d == "adv_set_force_channel":
        await state.set_state(AdminStates.waiting_for_force_channel_id)
        current = await database.get_setting('force_channel_id', 'غير محدد')
        await cq.message.edit_text(f"🔗 **تحديد قناة الإشتراك:**\n\nالحالية: `{current}`\n\nأرسل الآن ID القناة.", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 إلغاء", callback_data="back_to_advanced")))
        return
        
    await cq.answer("⚠️ هذه الميزة قيد الإنشاء.", show_alert=True)

def register_advanced_panel_handler(dp: Dispatcher):
    dp.register_message_handler(advanced_panel_cmd, is_admin, commands=['hijri'], state="*")
    dp.register_callback_query_handler(advanced_callbacks_cmd, is_admin, lambda c: c.data.startswith("adv_"), state="*")
