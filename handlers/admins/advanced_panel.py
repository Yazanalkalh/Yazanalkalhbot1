from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from config import ADMIN_CHAT_ID
import data_store
from loader import bot
# Import the keyboard designers
from keyboards.inline.advanced_keyboards import create_advanced_panel, get_advanced_submenu
# Import all necessary database functions
from utils.database import (
    get_all_library_content, delete_content_by_id,
    get_pending_channels, approve_channel, reject_channel, get_approved_channels,
    get_db_stats,
)
from states.admin_states import AdminStates

# This is the new, fully functional "Engine Room Manager". It handles the /hijri command
# and contains the complete logic for ALL advanced features.

def is_admin(message: types.Message):
    """A filter to check if the user is an admin."""
    return message.from_user.id == ADMIN_CHAT_ID

async def advanced_panel_cmd(m: types.Message, state: FSMContext):
    """Handler for the new /hijri command."""
    if await state.get_state() is not None:
        await state.finish()
    await m.reply(
        "🛠️ **لوحة التحكم المتقدمة (غرفة المحركات)**\n\nتحكم في الإعدادات المتقدمة والأنظمة الأساسية للبوت.",
        reply_markup=create_advanced_panel()
    )

async def advanced_callbacks_cmd(cq: types.CallbackQuery, state: FSMContext):
    """Central handler for all callback queries from the advanced panel."""
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
        key, feature_name, target_dict = toggle_map[d]
        target_dict[key] = not target_dict.get(key, False)
        data_store.save_data()
        reply_markup = get_advanced_submenu("adv_notifications") if 'notify' in d else create_advanced_panel()
        await cq.message.edit_reply_markup(reply_markup)
        status_text = "تفعيل" if target_dict[key] else "تعطيل"
        await cq.answer(f"✅ تم {status_text} ميزة '{feature_name}'.")
        return

    # --- Logic for Sub-Menus ---
    sub_menus = ["adv_notifications", "adv_manage_library", "adv_manage_channels", "adv_stats"]
    if d in sub_menus:
        menu_titles = {
            "adv_notifications": "🔔 **إعدادات الإشعارات**", "adv_manage_library": "📚 **إدارة مكتبة المحتوى**",
            "adv_manage_channels": "🌐 **إدارة القنوات والمجموعات**", "adv_stats": "📊 **قسم الإحصائيات**"
        }
        await cq.message.edit_text(menu_titles[d], reply_markup=get_advanced_submenu(d))
        return

    # --- Logic for System Status ---
    if d == "adv_system_status":
        stats = get_db_stats()
        text = (
            f"🔬 **مراقبة حالة النظام**\n\n"
            f"▫️ **حالة DB:** {'متصلة ✅' if stats.get('ok') else 'غير متصلة ❌'}\n"
            f"▫️ **المحتوى المحفوظ:** {stats.get('library_count', 0)} عنصر\n"
            f"▫️ **المجدول:** {stats.get('scheduled_count', 0)} منشور\n"
            f"▫️ **المستخدمون:** {stats.get('users_count', 0)} مستخدم"
        )
        await cq.message.edit_text(text, reply_markup=get_advanced_submenu("back_to_advanced").add(types.InlineKeyboardButton("🔙 العودة", callback_data="back_to_advanced")))
        return
        
    # --- Logic for Library Management ---
    if d == "adv_view_library":
        content_list = get_all_library_content(limit=20)
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        text = "📚 **محتويات المكتبة (آخر 20):**\nاضغط على عنصر لحذفه."
        if not content_list:
            text = "📚 **مكتبة المحتوى فارغة حاليًا.**"
        else:
            for item in content_list:
                snippet = item.get('value', '')[:40].replace('\n', ' ') + "..."
                keyboard.add(types.InlineKeyboardButton(f"🗑️ `{item.get('type')}`: {snippet}", callback_data=f"adv_delete_lib_{item.get('_id')}"))
        keyboard.add(types.InlineKeyboardButton("🔙 العودة", callback_data="adv_manage_library"))
        await cq.message.edit_text(text, reply_markup=keyboard)
        return

    if d.startswith("adv_delete_lib_"):
        content_id = d.replace("adv_delete_lib_", "")
        delete_content_by_id(content_id)
        await cq.answer("✅ تم الحذف.", show_alert=True)
        cq.data = "adv_view_library" 
        await advanced_callbacks_cmd(cq, state)
        return
        
    # --- Logic for Channel Management ---
    if d == "adv_view_pending_channels":
        pending = get_pending_channels()
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        text = "⏳ **قائمة طلبات الانضمام:**"
        if not pending:
            text = "✅ **لا توجد طلبات انضمام جديدة.**"
        else:
            for chat in pending:
                keyboard.add(types.InlineKeyboardButton(f"❓ {chat['title']}", callback_data=f"adv_review_{chat['_id']}"))
        keyboard.add(types.InlineKeyboardButton("🔙 العودة", callback_data="adv_manage_channels"))
        await cq.message.edit_text(text, reply_markup=keyboard)
        return
    
    if d.startswith("adv_review_"):
        chat_id = int(d.replace("adv_review_", ""))
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("✅ موافقة", callback_data=f"adv_approve_{chat_id}"),
            types.InlineKeyboardButton("❌ رفض", callback_data=f"adv_reject_{chat_id}")
        )
        await cq.message.edit_text(f"هل توافق على انضمام البوت إلى `{chat_id}`؟", reply_markup=keyboard)
        return

    if d.startswith("adv_approve_"):
        chat_id = int(d.replace("adv_approve_", ""))
        approve_channel(chat_id)
        await cq.message.edit_text("✅ تمت الموافقة على القناة.", reply_markup=get_advanced_submenu("adv_manage_channels"))
        return

    if d.startswith("adv_reject_"):
        chat_id = int(d.replace("adv_reject_", ""))
        reject_channel(chat_id)
        await cq.message.edit_text("❌ تم رفض القناة.", reply_markup=get_advanced_submenu("adv_manage_channels"))
        return

    if d == "adv_set_force_channel":
        await state.set_state(AdminStates.waiting_for_force_channel_id)
        current_ch = settings.get('force_channel_id', 'غير محدد')
        await cq.message.edit_text(f"🔗 **تحديد قناة الإشتراك الإجباري:**\n\nالقناة الحالية: `{current_ch}`\n\nأرسل الآن ID القناة (مع @ أو -).")
        return

def register_advanced_panel_handler(dp: Dispatcher):
    dp.register_message_handler(advanced_panel_cmd, is_admin, commands=['hijri'], state="*")
    dp.register_callback_query_handler(advanced_callbacks_cmd, is_admin, lambda c: c.data.startswith("adv_"), state="*")
