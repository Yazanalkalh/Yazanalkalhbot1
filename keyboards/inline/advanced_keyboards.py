from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# ✅ تم الإصلاح: لا يوجد data_store، نستخدم قاعدة البيانات مباشرة
from utils import database

def create_advanced_panel() -> InlineKeyboardMarkup:
    """
    ✅ تم الإصلاح: تنشئ لوحة المفاتيح بناءً على أحدث الإعدادات من قاعدة البيانات مباشرة.
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # نقوم بجلب كل إعداد على حدة لضمان الحصول على أحدث قيمة
    maintenance_on = database.get_setting('maintenance_mode', False)
    antispam_on = database.get_setting('anti_duplicate_mode', False)
    force_sub_on = database.get_setting('force_subscribe', False)

    maintenance_status = "🟢 تشغيل البوت" if maintenance_on else "🔴 إيقاف البوت (صيانة)"
    antispam_status = "🔕 تعطيل منع التكرار" if antispam_on else "🔔 تفعيل منع التكرار"
    force_sub_status = "🔗 تعطيل الاشتراك الإجباري" if force_sub_on else "🔗 تفعيل الاشتراك الإجباري"

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

def get_advanced_submenu(menu_type: str) -> InlineKeyboardMarkup:
    """
    ✅ تم الإصلاح: تنشئ القوائم الفرعية بناءً على أحدث الإعدادات من قاعدة البيانات.
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # منطق خاص لقائمة الإشعارات لجلب الإعدادات المباشرة
    if menu_type == "adv_notifications":
        notify_success_on = database.get_setting('notification_on_success', False)
        notify_fail_on = database.get_setting('notification_on_fail', False)
        
        buttons_data = [
            ("🔴 تعطيل إشعار النجاح" if notify_success_on else "🟢 تفعيل إشعار النجاح", "adv_toggle_success_notify"),
            ("🔴 تعطيل إشعار الفشل" if notify_fail_on else "🟢 تفعيل إشعار الفشل", "adv_toggle_fail_notify")
        ]
    else:
        # بقية القوائم لا تعتمد على الحالة، لذا تبقى كما هي
        buttons_map = {
            "adv_manage_library": [("📖 عرض كل المحتوى", "adv_view_library"), ("🧹 حذف المحتوى غير المستخدم", "adv_prune_library")],
            "adv_manage_channels": [("📋 عرض القنوات المعتمدة", "adv_view_channels"), ("⏳ عرض طلبات الانضمام", "adv_view_pending_channels"), ("🆔 تحديد قناة الاشتراك الإجباري", "adv_set_force_channel")],
            "adv_stats": [("📈 نمو المستخدمين (آخر 7 أيام)", "adv_stats_growth"), ("🏆 المستخدمون الأكثر تفاعلاً", "adv_stats_top_users")]
        }
        buttons_data = buttons_map.get(menu_type, [])

    buttons = [InlineKeyboardButton(text=text, callback_data=cb) for text, cb in buttons_data]
    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton(text="🔙 العودة للوحة المتقدمة", callback_data="back_to_advanced"))
    return keyboard
