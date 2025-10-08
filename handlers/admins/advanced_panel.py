from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from config import ADMIN_CHAT_ID
# ✅ تم الإصلاح: لا يوجد data_store هنا
from keyboards.inline.advanced_keyboards import create_advanced_panel, get_advanced_submenu
from utils import database, texts
from states.admin_states import AdminStates

def is_admin(message: types.Message):
    return message.from_user.id == ADMIN_CHAT_ID

async def advanced_panel_cmd(m: types.Message, state: FSMContext):
    if await state.get_state() is not None: await state.finish()
    await m.reply(texts.get_text("adv_panel_title"), reply_markup=create_advanced_panel())

async def advanced_callbacks_cmd(cq: types.CallbackQuery, state: FSMContext):
    await cq.answer()
    d = cq.data

    if d == "back_to_advanced":
        await cq.message.edit_text(texts.get_text("adv_panel_title"), reply_markup=create_advanced_panel())
        return

    # ✅ تم الإصلاح: منطق جديد لمفاتيح الإعدادات، يتعامل مباشرة مع قاعدة البيانات
    toggle_map = {
        "adv_toggle_maintenance": ("maintenance_mode", "وضع الصيانة"),
        "adv_toggle_antispam": ("anti_duplicate_mode", "منع التكرار"),
        "adv_toggle_force_sub": ("force_subscribe", "الاشتراك الإجباري"),
        "adv_toggle_success_notify": ("notification_on_success", "إشعار النجاح"),
        "adv_toggle_fail_notify": ("notification_on_fail", "إشعار الفشل")
    }
    if d in toggle_map:
        key, name = toggle_map[d]
        # نقوم بجلب القيمة الحالية، وعكسها، ثم تحديثها في عملية واحدة
        current_value = database.get_setting(key, False)
        new_value = not current_value
        database.update_setting(key, new_value)
        
        # تحديث لوحة المفاتيح
        markup = get_advanced_submenu("adv_notifications") if 'notify' in d else create_advanced_panel()
        await cq.message.edit_reply_markup(markup)
        status = "تفعيل" if new_value else "تعطيل"
        await cq.answer(texts.get_text("adv_toggle_success", status=status, feature_name=name))
        return

    # --- إدارة المكتبة ---
    if d == "adv_view_library":
        content_list = database.get_all_library_content(20)
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        text = "📚 **محتويات المكتبة (آخر 20):**\nاضغط على عنصر لحذفه."
        if not content_list:
            text = "📚 **مكتبة المحتوى فارغة حاليًا.**"
        else:
            for item in content_list:
                snippet = item.get('value', '')[:40].replace('\n', ' ') + "..."
                # ✅ تم الإصلاح: نستخدم المعرّف الفريد (_id) في callback data لضمان الحذف الآمن
                keyboard.add(types.InlineKeyboardButton(f"🗑️ `{item.get('type')}`: {snippet}", callback_data=f"adv_delete_lib_id_{item['_id']}"))
        keyboard.add(types.InlineKeyboardButton("🔙 العودة", callback_data="adv_manage_library"))
        await cq.message.edit_text(text, reply_markup=keyboard)
        return

    if d.startswith("adv_delete_lib_id_"):
        # ✅ تم الإصلاح: الحذف الآن آمن 100% باستخدام المعرّف الفريد
        item_id = d.replace("adv_delete_lib_id_", "")
        database.delete_content_by_id(item_id)
        await cq.answer("✅ تم الحذف.", show_alert=True)
        # تحديث العرض
        cq.data = "adv_view_library"
        await advanced_callbacks_cmd(cq, state)
        return

    # --- تحديد قناة الاشتراك الإجباري ---
    if d == "adv_set_force_channel":
        await state.set_state(AdminStates.waiting_for_force_channel_id)
        # ✅ تم الإصلاح: جلب الإعداد الحالي مباشرة من قاعدة البيانات
        current = database.get_setting('force_channel_id', 'غير محدد')
        await cq.message.edit_text(f"🔗 **تحديد قناة الاشتراك:**\n\nالحالية: `{current}`\n\nأرسل الآن ID القناة.", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 إلغاء", callback_data="back_to_advanced")))
        return
        
    # --- الأجزاء الأخرى (لا تحتاج لتغيير لأنها تستخدم قاعدة البيانات بالفعل) ---
    sub_menus = ["adv_notifications", "adv_manage_library", "adv_manage_channels", "adv_stats"]
    if d in sub_menus:
        # ... (هذا الجزء يبقى كما هو)
        titles = {
            "adv_notifications": "🔔 **إعدادات الإشعارات**", "adv_manage_library": "📚 **إدارة مكتبة المحتوى**",
            "adv_manage_channels": "🌐 **إدارة القنوات والمجموعات**", "adv_stats": "📊 **قسم الإحصائيات**"
        }
        await cq.message.edit_text(titles[d], reply_markup=get_advanced_submenu(d))
        return
    if d == "adv_system_status":
        # ... (هذا الجزء يبقى كما هو)
        stats = database.get_db_stats()
        text = (f"🔬 **مراقبة حالة النظام**\n\n"
                f"▫️ **DB:** {'متصلة ✅' if stats.get('ok') else '❌'}\n"
                f"▫️ **المحتوى:** {stats.get('library_count', 0)} عنصر\n"
                f"▫️ **المجدول:** {stats.get('scheduled_count', 0)} منشور\n"
                f"▫️ **المستخدمون:** {stats.get('users_count', 0)} مستخدم")
        await cq.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(texts.get_text("back_to_advanced_panel"), callback_data="back_to_advanced")))
        return
    # --- إدارة القنوات (تبقى كما هي) ---
    if d == "adv_view_pending_channels":
        # ... (هذا الجزء يبقى كما هو)
        pending = database.get_pending_channels()
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        text = "⏳ **قائمة طلبات الانضمام:**"
        if not pending: text = "✅ **لا توجد طلبات جديدة.**"
        else:
            for chat in pending:
                keyboard.add(types.InlineKeyboardButton(f"❓ {chat['title']}", callback_data=f"adv_review_{chat['_id']}"))
        keyboard.add(types.InlineKeyboardButton("🔙 العودة", callback_data="adv_manage_channels"))
        await cq.message.edit_text(text, reply_markup=keyboard)
        return
    # ... (بقية معالجات القنوات تبقى كما هي)
    if d.startswith("adv_review_"):
        chat_id = int(d.replace("adv_review_", "")); keyboard = types.InlineKeyboardMarkup(row_width=2); keyboard.add(types.InlineKeyboardButton("✅ موافقة", callback_data=f"adv_approve_{chat_id}"), types.InlineKeyboardButton("❌ رفض", callback_data=f"adv_reject_{chat_id}")); await cq.message.edit_text(f"هل توافق على انضمام البوت إلى `{chat_id}`؟", reply_markup=keyboard); return
    if d.startswith("adv_approve_"):
        chat_id = int(d.replace("adv_approve_", "")); database.approve_channel(chat_id); await cq.message.edit_text("✅ تمت الموافقة.", reply_markup=get_advanced_submenu("adv_manage_channels")); return
    if d.startswith("adv_reject_"):
        chat_id = int(d.replace("adv_reject_", "")); database.reject_channel(chat_id); await cq.message.edit_text("❌ تم الرفض.", reply_markup=get_advanced_submenu("adv_manage_channels")); return


def register_advanced_panel_handler(dp: Dispatcher):
    dp.register_message_handler(advanced_panel_cmd, is_admin, commands=['hijri'], state="*")
    dp.register_callback_query_handler(advanced_callbacks_cmd, is_admin, lambda c: c.data.startswith("adv_"), state="*")
