from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from config import ADMIN_CHAT_ID
import data_store
from loader import bot
# NEW: Import the new keyboard designer and sub-menus
from keyboards.inline.advanced_keyboards import create_advanced_panel, get_advanced_submenu
# NEW: We will need database functions later, so we import them now
from utils.database import (
    get_all_library_content, delete_content_by_id,
    get_pending_channels, approve_channel, reject_channel, get_approved_channels,
    get_db_stats,
)
from states.admin_states import AdminStates

# This is a new, isolated file. It handles the /hijri command and ALL advanced features.

def is_admin(message: types.Message):
    """A filter to check if the user is an admin."""
    return message.from_user.id == ADMIN_CHAT_ID

async def advanced_panel_cmd(m: types.Message, state: FSMContext):
    """
    Handler for the new /hijri command.
    It displays the advanced control panel.
    """
    if await state.get_state() is not None:
        await state.finish() # Ensure we exit any previous state
    
    await m.reply(
        "🛠️ **لوحة التحكم المتقدمة (غرفة المحركات)**\n\n"
        "هنا يمكنك التحكم في الإعدادات المتقدمة والأنظمة الأساسية للبوت.",
        reply_markup=create_advanced_panel()
    )

async def advanced_callbacks_cmd(cq: types.CallbackQuery, state: FSMContext):
    """
    Central handler for all callback queries from the advanced panel.
    It identifies them by the "adv_" prefix.
    """
    await cq.answer() # Acknowledge the button press
    
    d = cq.data
    settings = data_store.bot_data.setdefault('bot_settings', {})
    notification_settings = data_store.bot_data.setdefault('notification_settings', {})

    if d == "back_to_advanced":
        await cq.message.edit_text(
            "🛠️ **لوحة التحكم المتقدمة (غرفة المحركات)**",
            reply_markup=create_advanced_panel()
        )
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
        current_status = target_dict.get(key, False)
        target_dict[key] = not current_status
        data_store.save_data()
        
        # Refresh the keyboard to show the new status
        reply_markup = get_advanced_submenu("adv_notifications") if 'notify' in d else create_advanced_panel()
        await cq.message.edit_reply_markup(reply_markup)
        
        status_text = "تفعيل" if target_dict[key] else "تعطيل"
        await cq.answer(f"✅ تم {status_text} ميزة '{feature_name}'.")
        return

    # --- Logic for Sub-Menus ---
    sub_menus = ["adv_notifications", "adv_manage_library", "adv_manage_channels", "adv_stats"]
    if d in sub_menus:
        menu_titles = {
            "adv_notifications": "🔔 **إعدادات الإشعارات**\n\nاختر الإشعار الذي تريد تفعيله أو تعطيله:",
            "adv_manage_library": "📚 **إدارة مكتبة المحتوى**\n\nاختر الإجراء المطلوب:",
            "adv_manage_channels": "🌐 **إدارة القنوات والمجموعات**\n\nاختر الإجراء المطلوب:",
            "adv_stats": "📊 **قسم الإحصائيات**\n\nاختر التقرير الذي تريد عرضه:"
        }
        await cq.message.edit_text(menu_titles[d], reply_markup=get_advanced_submenu(d))
        return

    # --- Logic for System Status ---
    if d == "adv_system_status":
        try:
            stats = get_db_stats()
            # This part requires Render's environment variable for memory, which we don't have.
            # We will show database stats only.
            text = (
                "🔬 **مراقبة حالة النظام**\n\n"
                f"▫️ **حالة قاعدة البيانات:** {'متصلة ✅' if stats.get('ok') else 'غير متصلة ❌'}\n"
                f"▫️ **إجمالي المحتوى المحفوظ:** {stats.get('library_count', 'N/A')} عنصر\n"
                f"▫️ **المنشورات المجدولة:** {stats.get('scheduled_count', 'N/A')} منشور\n"
                f"▫️ **إجمالي المستخدمين المسجلين:** {stats.get('users_count', 'N/A')} مستخدم\n"
            )
        except Exception as e:
            text = f"❌ حدث خطأ أثناء فحص حالة النظام: {e}"
        
        await cq.message.edit_text(text, reply_markup=get_advanced_submenu(d).add(InlineKeyboardButton("🔙 العودة للوحة المتقدمة", callback_data="back_to_advanced")))
        return
        
    # --- Logic for Library Management ---
    if d == "adv_view_library":
        content_list = get_all_library_content(limit=10)
        if not content_list:
            text = "📚 **مكتبة المحتوى فارغة حاليًا.**"
        else:
            text = "📚 **محتويات المكتبة (آخر 10 عناصر):**\n\n"
            keyboard = InlineKeyboardMarkup(row_width=1)
            for item in content_list:
                content_snippet = item.get('value', 'N/A')
                if len(content_snippet) > 40:
                    content_snippet = content_snippet[:40] + "..."
                # Each item gets a delete button with a unique callback
                keyboard.add(InlineKeyboardButton(
                    f"🗑️ حذف: `{item.get('type')}` - {content_snippet}", 
                    callback_data=f"adv_delete_lib_{item.get('_id')}"
                ))
            keyboard.add(InlineKeyboardButton("🔙 العودة للوحة المتقدمة", callback_data="back_to_advanced"))
            await cq.message.edit_text(text, reply_markup=keyboard)
            return

    # Handler for the actual deletion from the library
    if d.startswith("adv_delete_lib_"):
        content_id = d.replace("adv_delete_lib_", "")
        delete_content_by_id(content_id)
        await cq.answer("✅ تم حذف العنصر من المكتبة بنجاح.", show_alert=True)
        # Refresh the library view
        await cq.message.edit_text("⏳ جاري تحديث المكتبة...", reply_markup=None)
        await advanced_callbacks_cmd(cq, state) # Simulate clicking the view button again
        return

    # --- Logic for Channel Management ---
    if d == "adv_view_pending_channels":
        pending_list = get_pending_channels()
        if not pending_list:
            text = "✅ **لا توجد طلبات انضمام جديدة.**"
            await cq.message.edit_text(text, reply_markup=get_advanced_submenu("adv_manage_channels"))
        else:
            text = "⏳ **قائمة طلبات الانضمام:**\n\nاضغط على اسم القناة للموافقة أو الرفض."
            keyboard = InlineKeyboardMarkup(row_width=1)
            for chat in pending_list:
                keyboard.add(InlineKeyboardButton(f"{chat['title']}", callback_data=f"adv_review_chat_{chat['_id']}"))
            keyboard.add(InlineKeyboardButton("🔙 العودة", callback_data="adv_manage_channels"))
            await cq.message.edit_text(text, reply_markup=keyboard)
        return

    # --- This is just a placeholder, the real logic would be more complex ---
    await cq.answer("هذه الميزة جاهزة للتفعيل في الملفات القادمة.", show_alert=True)


def register_advanced_panel_handler(dp: Dispatcher):
    """Registers the handlers for the advanced panel."""
    dp.register_message_handler(advanced_panel_cmd, is_admin, commands=['hijri'], state="*")
    dp.register_callback_query_handler(advanced_callbacks_cmd, is_admin, lambda c: c.data.startswith("adv_"), state="*")
