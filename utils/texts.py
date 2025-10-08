# ✅ تم الإصلاح: لم نعد نستخدم data_store، نستخدم قاعدة البيانات مباشرة
from utils import database

# هذا القاموس يحتوي على النصوص الافتراضية، وهذا صحيح 100%
TEXTS = {
    # Key: { "description": "Arabic Label for the button", "default": "The actual text with placeholders" }
    
    # --- General UI & Actions ---
    "action_cancelled": {"description": "رسالة إلغاء العملية", "default": "✅ تم إلغاء العملية بنجاح."},
    "back_to_main_panel": {"description": "نص زر العودة للوحة الرئيسية", "default": "🔙 العودة إلى اللوحة الرئيسية"},
    
    # --- User-Facing Messages ---
    "user_welcome": {"description": "رسالة الترحيب بالمستخدم", "default": "👋 أهلًا وسهلًا بك يا #name!\nأنا هنا لخدمتك."},
    "user_default_reply": {"description": "الرد الافتراضي للمستخدم", "default": "✅ تم استلام رسالتك بنجاح، شكراً لتواصلك."},
    "user_force_subscribe": {"description": "رسالة طلب الاشتراك الإجباري", "default": "عذرًا, لاستخدام هذا البوت, يرجى الاشتراك أولاً في قناتنا."},
    "user_maintenance_mode": {"description": "رسالة وضع الصيانة للمستخدم", "default": "عذراً، البوت قيد الصيانة حالياً. سنعود قريباً."},


    # --- Admin Panel Titles ---
    "admin_panel_title": {"description": "عنوان لوحة /admin", "default": "🔧 **لوحة التحكم الإدارية**"},
    "adv_panel_title": {"description": "عنوان لوحة /hijri", "default": "🛠️ **لوحة التحكم المتقدمة (غرفة المحركات)**"},
    
    # --- Text Manager Feature Texts ---
    "text_manager_title": {"description": "عنوان قائمة مدير النصوص", "default": "✏️ **مدير النصوص الملكي**\n\nاختر النص الذي تريد تعديله:"},
    "text_manager_prompt_new": {"description": "رسالة طلب النص الجديد", "default": "النص الحالي لـ `{text_name}` هو:\n`{current_text}`\n\nأرسل الآن النص الجديد:"},
    "text_manager_success": {"description": "رسالة نجاح تحديث النص", "default": "✅ تم تحديث النص `{text_name}` بنجاح."},
    
    # ... يمكنك إضافة المزيد من النصوص هنا
}

def get_text(key: str, **kwargs) -> str:
    """
    ✅ تم الإصلاح: هذه الدالة الآن تجلب النصوص المخصصة مباشرة من قاعدة البيانات.
    """
    # نقوم بجلب أحدث نسخة من النصوص المخصصة من قاعدة البيانات
    custom_texts = database.get_setting('custom_texts', {})
    
    # نبحث عن القالب الافتراضي في القاموس الثابت
    default_template = TEXTS.get(key, {}).get("default", f"_{key}_")
    
    # نستخدم النص المخصص إذا كان موجودًا، وإلا نعود إلى الافتراضي
    text_template = custom_texts.get(key, default_template)
    
    try:
        # نقوم بملء أي متغيرات مثل {name}
        return text_template.format(**kwargs)
    except (KeyError, ValueError):
        # في حال وجود خطأ في التنسيق، نعيد النص كما هو
        return text_template

def get_all_text_descriptions() -> list:
    """(لا تغييرات هنا، هذه الدالة سليمة)"""
    return sorted([(key, details["description"]) for key, details in TEXTS.items()])
