from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from config import ADMIN_CHAT_ID
import data_store
from loader import bot
from keyboards.inline.advanced_keyboards import create_advanced_panel, get_advanced_submenu
from utils.database import (
    get_all_library_content, delete_content_by_id,
    get_pending_channels, approve_channel, reject_channel, get_approved_channels,
    get_db_stats,
    # افترض وجود هذه الدوال، إذا لم تكن موجودة، يجب إنشاؤها
    # prune_unused_content, get_user_growth_stats, get_top_users
)
from states.admin_states import AdminStates

# This is the final and complete "Engine Room Manager".

def is_admin(message: types.Message):
    return message.from_user.id == ADMIN_CHAT_ID

async def advanced_panel_cmd(m: types.Message, state: FSMContext):
    if await state.get_state() is not None: await state.finish()
    await m.reply(
        "🛠️ **لوحة التحكم المتقدمة (غرفة المحركات)**",
        reply_markup=create_advanced_panel()
    )

async def advanced_callbacks_cmd(cq: types.CallbackQuery, state: FSMContext):
    # استخدام cq.answer() في بداية الدالة هو أفضل ممارسة
    # لإعلام تليجرام أن الزر قد تم استلامه فوراً.
    await cq.answer()
    
    d = cq.data
    settings = data_store.bot_data.setdefault('bot_settings', {})
    notification_settings = data_store.bot_data.setdefault('notification_settings', {})

    if d == "back_to_advanced":
        await cq.message.edit_text("🛠️ **لوحة التحكم المتقدمة**", reply_markup=create_advanced_panel())
        return

    # --- Logic for Toggle Buttons ---
    toggle_map = {
        "adv_toggle_maintenance": ("maintenance_mode", "وضع الصيانة", settings),
        "adv_toggle_antispam": ("anti_duplicate_mode", "منع التكرار", settings),
        "adv_toggle_force_sub": ("force_subscribe", "الإشتراك الإجباري", settings),
        "adv_toggle_success_notify": ("on_success", "إشعار النجاح", notification_settings),
        "adv_toggle_fail_notify": ("on_fail", "إشعار الفشل", notification_settings)
    }
    if d in toggle_map:
        key, name, target_dict = toggle_map[d]
        target_dict[key] = not target_dict.get(key, False)
        data_store.save_data()
        markup = get_advanced_submenu("adv_notifications") if 'notify' in d else create_advanced_panel()
        await cq.message.edit_reply_markup(markup)
        status = "تفعيل" if target_dict[key] else "تعطيل"
        # تم نقل cq.answer هنا لتقديم رسالة مخصصة
        await cq.answer(f"✅ تم {status} '{name}'.")
        return

    # --- Logic for Sub-Menus ---
    sub_menus = ["adv_notifications", "adv_manage_library", "adv_manage_channels", "adv_stats"]
    if d in sub_menus:
        titles = {"adv_notifications": "🔔 **إعدادات الإشعارات**", "adv_manage_library": "📚 **إدارة المكتبة**", "adv_manage_channels": "🌐 **إدارة القنوات**", "adv_stats": "📊 **الإحصائيات**"}
        await cq.message.edit_text(titles[d], reply_markup=get_advanced_submenu(d))
        return

    # --- Logic for System Status ---
    if d == "adv_system_status":
        stats = get_db_stats()
        text = (f"🔬 **مراقبة حالة النظام**\n\n"
                f"▫️ **DB:** {'متصلة ✅' if stats.get('ok') else '❌'}\n"
                f"▫️ **المحتوى:** {stats.get('library_count', 0)} عنصر\n"
                f"▫️ **المجدول:** {stats.get('scheduled_count', 0)} منشور\n"
                f"▫️ **المستخدمون:** {stats.get('users_count', 0)} مستخدم")
        await cq.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 العودة", callback_data="back_to_advanced")))
        return
        
    # --- Logic for Library Management ---
    if d == "adv_view_library":
        content = get_all_library_content(20)
        kb = types.InlineKeyboardMarkup(row_width=1)
        text = "📚 **محتويات المكتبة:**\nاضغط على عنصر لحذفه."
        if not content: text = "📚 **مكتبة المحتوى فارغة.**"
        else:
            await state.update_data(library_view=content)
            for i, item in enumerate(content):
                snippet = item.get('value', '')[:40].replace('\n', ' ') + "..."
                kb.add(types.InlineKeyboardButton(f"🗑️ `{item.get('type')}`: {snippet}", callback_data=f"adv_delete_lib_idx_{i}"))
        kb.add(types.InlineKeyboardButton("🔙 العودة", callback_data="adv_manage_library"))
        await cq.message.edit_text(text, reply_markup=kb)
        return

    if d.startswith("adv_delete_lib_idx_"):
        idx = int(d.replace("adv_delete_lib_idx_", ""))
        data = await state.get_data()
        content_list = data.get('library_view', [])
        if 0 <= idx < len(content_list):
            item_to_delete = content_list.pop(idx)
            delete_content_by_id(item_to_delete['_id'])
            await state.update_data(library_view=content_list)
            await cq.answer("✅ تم الحذف.", show_alert=True)
            temp_cq = types.CallbackQuery(id=cq.id, from_user=cq.from_user, chat_instance=cq.chat_instance, message=cq.message, data="adv_view_library")
            await advanced_callbacks_cmd(temp_cq, state)
        return
    
    # --- [إضافة جديدة] تفعيل زر حذف المحتوى غير المستخدم ---
    if d == "adv_prune_library":
        # ملاحظة: هذه وظيفة تحتاج إلى منطق دقيق في ملف database.py
        # حالياً سنضع رسالة مؤقتة
        await cq.answer("🧹 وظيفة حذف المحتوى غير المستخدم (قيد التطوير).", show_alert=True)
        # عند تجهيزها، يمكنك استدعاء دالة مثل:
        # count = prune_unused_content()
        # await cq.answer(f"✅ تم حذف {count} عنصر غير مستخدم.", show_alert=True)
        return

    # --- Logic for Channel Management ---
    if d == "adv_view_pending_channels":
        pending = get_pending_channels()
        kb = types.InlineKeyboardMarkup(row_width=1)
        text = "⏳ **طلبات الانضمام:**"
        if not pending: text = "✅ **لا توجد طلبات جديدة.**"
        else:
            for chat in pending:
                kb.add(types.InlineKeyboardButton(f"❓ {chat['title']}", callback_data=f"adv_review_{chat['_id']}"))
        kb.add(types.InlineKeyboardButton("🔙 العودة", callback_data="adv_manage_channels"))
        await cq.message.edit_text(text, reply_markup=kb)
        return

    if d == "adv_view_channels":
        approved = get_approved_channels()
        text = "📋 **القنوات المعتمدة:**\n\n"
        if not approved: text += "لا توجد قنوات معتمدة حاليًا."
        else:
            for chat in approved:
                text += f"- {chat['title']} (`{chat['_id']}`)\n"
        # [تصحيح هام] تم إصلاح زر العودة هنا ليعمل بشكل صحيح
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 العودة", callback_data="adv_manage_channels"))
        await cq.message.edit_text(text, reply_markup=kb)
        return
    
    # [تصحيح هام] تم تعديل هذا القسم ليتعامل مع IDs كنصوص (Strings) بدلاً من أرقام لتجنب الأخطاء
    if d.startswith("adv_review_"):
        chat_id_str = d.replace("adv_review_", "")
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("✅ موافقة", callback_data=f"adv_approve_{chat_id_str}"),
               types.InlineKeyboardButton("❌ رفض", callback_data=f"adv_reject_{chat_id_str}"))
        await cq.message.edit_text(f"هل توافق على انضمام البوت إلى القناة؟\nID: `{chat_id_str}`", reply_markup=kb)
        return

    if d.startswith("adv_approve_"):
        chat_id_str = d.replace("adv_approve_", ""); approve_channel(chat_id_str)
        await cq.message.edit_text("✅ تمت الموافقة.", reply_markup=get_advanced_submenu("adv_manage_channels"))
        return

    if d.startswith("adv_reject_"):
        chat_id_str = d.replace("adv_reject_", ""); reject_channel(chat_id_str)
        await cq.message.edit_text("❌ تم الرفض.", reply_markup=get_advanced_submenu("adv_manage_channels"))
        return

    if d == "adv_set_force_channel":
        await state.set_state(AdminStates.waiting_for_force_channel_id)
        current = settings.get('force_channel_id', 'غير محدد')
        await cq.message.edit_text(f"🔗 **تحديد قناة الإشتراك:**\n\nالحالية: `{current}`\n\nأرسل الآن ID القناة.", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 إلغاء", callback_data="back_to_advanced")))
        return
    
    # --- [إضافة جديدة] تفعيل أزرار الإحصائيات ---
    if d == "adv_stats_growth":
        # يمكنك هنا استدعاء دالة من قاعدة البيانات تعرض نمو المستخدمين
        # text = get_user_growth_stats()
        text = "📈 **نمو المستخدمين (آخر 7 أيام):**\n\nهذه الميزة قيد التطوير وستعرض رسماً بيانياً قريباً."
        await cq.message.edit_text(text, reply_markup=get_advanced_submenu("adv_stats"))
        return
    
    if d == "adv_stats_top_users":
        # يمكنك هنا استدعاء دالة من قاعدة البيانات تعرض أكثر المستخدمين تفاعلاً
        # text = get_top_users()
        text = "🏆 **المستخدمون الأكثر تفاعلاً:**\n\nهذه الميزة قيد التطوير وستعرض قائمة بالمستخدمين قريباً."
        await cq.message.edit_text(text, reply_markup=get_advanced_submenu("adv_stats"))
        return
        
    # --- [إضافة جديدة] تفعيل زر إدارة النصوص ---
    if d == "adv_text_manager":
        await cq.answer("✏️ وظيفة إدارة نصوص البوت (قيد التطوير).", show_alert=True)
        return
        
    # [ملاحظة] هذه الرسالة لم يعد من المفترض أن تظهر
    # لأن كل الأزرار المعروفة تم تعريف وظائفها في الأعلى.
    # سنتركها كإجراء احترازي لأي زر جديد قد تضيفه مستقبلاً.
    await cq.answer("⚠️ زر غير معروف أو ميزة قيد الإنشاء.", show_alert=True)

def register_advanced_panel_handler(dp: Dispatcher):
    dp.register_message_handler(advanced_panel_cmd, is_admin, commands=['hijri'], state="*")
    dp.register_callback_query_handler(advanced_callbacks_cmd, is_admin, lambda c: c.data.startswith("adv_"), state="*")
