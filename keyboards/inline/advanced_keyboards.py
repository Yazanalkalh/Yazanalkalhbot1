from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import data_store

# This is the final, definitive version of the advanced keyboard designer.

def create_advanced_panel() -> InlineKeyboardMarkup:
    """Creates the main keyboard for the advanced control panel."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    settings = data_store.bot_data.get('bot_settings', {})
    
    maintenance_status = "🟢 تشغيل البوت" if settings.get('maintenance_mode', False) else "🔴 إيقاف البوت (صيانة)"
    antispam_status = "🔕 تعطيل منع التكرار" if settings.get('anti_duplicate_mode', False) else "🔔 تفعيل منع التكرار"
    force_sub_status = "🔗 تعطيل الإشتراك الإجباري" if settings.get('force_subscribe', False) else "🔗 تفعيل الإشتراك الإجباري"

    keyboard.add(
        InlineKeyboardButton(maintenance_status, callback_data="adv_toggle_maintenance"),
        InlineKeyboardButton(antispam_status, callback_data="adv_toggle_antispam")
    )
    keyboard.add(
        InlineKeyboardButton("🔔 إعدادات الإشعارات", callback_data="adv_notifications"),
        InlineKeyboardButton("📚 إدارة مكتبة المحتوى", callback_data="adv_manage_library")
    )
    keyboard.add(
        InlineKeyboardButton(force_sub_status, callback_data="adv_toggle_force_sub"),
        InlineKeyboardButton("📊 قسم الإحصائيات", callback_data="adv_stats")
    )
    keyboard.add(
        InlineKeyboardButton("🌐 إدارة القنوات والمجموعات", callback_data="adv_manage_channels"),
        InlineKeyboardButton("🔬 مراقبة حالة النظام", callback_data="adv_system_status")
    )
    keyboard.add(
        InlineKeyboardButton("✏️ إدارة نصوص البوت", callback_data="adv_text_manager")
    )
    keyboard.add(
        InlineKeyboardButton("🔙 العودة إلى اللوحة الرئيسية", callback_data="back_to_main")
    )
    return keyboard

def get_advanced_submenu(menu_type: str) -> InlineKeyboardMarkup:
    """Generates specific sub-menus for the advanced panel."""
    keyboard = InlineKeyboardMarkup(row_width=1)
    notification_settings = data_store.bot_data.get('notification_settings', {})
    
    buttons_map = {
        "adv_notifications": [
            ("🟢 تفعيل إشعار النجاح" if not notification_settings.get('on_success', False) else "🔴 تعطيل إشعار النجاح", "adv_toggle_success_notify"),
            ("🟢 تفعيل إشعار الفشل" if not notification_settings.get('on_fail', False) else "🔴 تعطيل إشعار الفشل", "adv_toggle_fail_notify")
        ],
        "adv_manage_library": [
            ("📖 عرض كل المحتوى", "adv_view_library"),
            ("🧹 حذف المحتوى غير المستخدم", "adv_prune_library")
        ],
        "adv_manage_channels": [
            ("📋 عرض القنوات المعتمدة", "adv_view_channels"),
            ("⏳ عرض طلبات الانضمام", "adv_view_pending_channels"),
            ("🆔 تحديد قناة الاشتراك الإجباري", "adv_set_force_channel")
        ],
        "adv_stats": [
            ("📈 نمو المستخدمين (آخر 7 أيام)", "adv_stats_growth"),
            ("🏆 المستخدمون الأكثر تفاعلاً", "adv_stats_top_users")
        ]
    }
    
    buttons = [InlineKeyboardButton(text=text, callback_data=cb) for text, cb in buttons_map.get(menu_type, [])]
    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton(text="🔙 العودة للوحة المتقدمة", callback_data="back_to_advanced"))
    return keyboard
