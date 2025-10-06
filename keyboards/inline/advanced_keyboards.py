from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import data_store

# This is a new, isolated file. Its only job is to design the buttons
# for the new advanced control panel (/hijri).

def create_advanced_panel() -> InlineKeyboardMarkup:
    """
    Creates the main keyboard for the advanced control panel.
    Some buttons are dynamic and change their text based on current settings.
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Get current settings to display the correct button status
    settings = data_store.bot_data.get('bot_settings', {})
    
    # Dynamic button for Maintenance Mode
    maintenance_status = "🔴 تعطيل البوت (صيانة)" if not settings.get('maintenance_mode', False) else "🟢 تشغيل البوت"
    
    # Dynamic button for Anti-Spam
    antispam_status = "🔕 تعطيل وضع عدم الإزعاج" if settings.get('anti_duplicate_mode', False) else "🔔 تفعيل وضع عدم الإزعاج"

    # Dynamic button for Forced Subscription
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
    # Add a back button to the main /admin panel for convenience
    keyboard.add(
        InlineKeyboardButton("🔙 العودة إلى اللوحة الرئيسية", callback_data="back_to_main")
    )
    return keyboard

def get_advanced_submenu(menu_type: str) -> InlineKeyboardMarkup:
    """Generates specific sub-menus for the advanced panel."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    buttons_map = {
        "adv_notifications": [
            # In the future, we can make these dynamic too
            ("켜기 إشعار النشر الناجح", "adv_toggle_success_notify"),
            ("켜기 إشعار فشل النشر", "adv_toggle_fail_notify")
        ],
        "adv_manage_library": [
            ("📖 عرض محتوى المكتبة", "adv_view_library"),
            ("🧹 حذف المحتوى غير المستخدم", "adv_prune_library")
        ],
        "adv_manage_channels": [
            ("📋 عرض القنوات المعتمدة", "adv_view_channels"),
            ("⏳ عرض طلبات الانضمام", "adv_view_pending_channels")
        ],
        "adv_stats": [
            ("📈 نمو المستخدمين (آخر 7 أيام)", "adv_stats_growth"),
            ("🏆 المستخدمون الأكثر تفاعلاً", "adv_stats_top_users")
        ]
    }
    
    buttons = [InlineKeyboardButton(text=text, callback_data=cb) for text, cb in buttons_map.get(menu_type, [])]
    keyboard.add(*buttons)
    # Use a different back callback to return to the advanced panel, not the main one
    keyboard.add(InlineKeyboardButton(text="🔙 العودة للوحة المتقدمة", callback_data="back_to_advanced"))
    return keyboard
