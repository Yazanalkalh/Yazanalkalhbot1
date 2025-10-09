from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import database

async def create_advanced_panel() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    is_maintenance = await database.get_setting('maintenance_mode', False)
    is_antispam = await database.get_setting('anti_duplicate_mode', False)
    is_force_sub = await database.get_setting('force_subscribe', False)
    
    maintenance_status = "🟢 تشغيل البوت" if is_maintenance else "🔴 إيقاف البوت (صيانة)"
    antispam_status = "🔕 تعطيل منع التكرار" if is_antispam else "🔔 تفعيل منع التكرار"
    force_sub_status = "🔗 تعطيل الإشتراك الإجباري" if is_force_sub else "🔗 تفعيل الإشتراك الإجباري"

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
        InlineKeyboardButton("🔙 العودة إلى اللوحة الرئيسية", callback_data="back_to_main")
    )
    return keyboard

async def get_advanced_submenu(menu_type: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    if menu_type == "adv_notifications":
        on_success = await database.get_setting('notification_on_success', False)
        on_fail = await database.get_setting('notification_on_fail', False)
        buttons = [
            ("🟢 تفعيل إشعار النجاح" if not on_success else "🔴 تعطيل إشعار النجاح", "adv_toggle_success_notify"),
            ("🟢 تفعيل إشعار الفشل" if not on_fail else "🔴 تعطيل إشعار الفشل", "adv_toggle_fail_notify")
        ]
    else:
        buttons_map = {
            "adv_manage_library": [("📖 عرض كل المحتوى", "adv_view_library")],
            "adv_manage_channels": [
                ("📋 عرض القنوات المعتمدة", "adv_view_channels"),
                ("⏳ عرض طلبات الانضمام", "adv_view_pending_channels"),
                ("🆔 تحديد قناة الاشتراك الإجباري", "adv_set_force_channel")
            ],
            "adv_stats": [("📈 نمو المستخدمين (آخر 7 أيام)", "adv_stats_growth")]
        }
        buttons = buttons_map.get(menu_type, [])

    for text, cb in buttons:
        keyboard.add(InlineKeyboardButton(text=text, callback_data=cb))
        
    keyboard.add(InlineKeyboardButton(text="🔙 العودة للوحة المتقدمة", callback_data="back_to_advanced"))
    return keyboard
