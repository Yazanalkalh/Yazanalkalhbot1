import data_store

# This is the final, definitive version of the "Smart Dictionary".
# The placeholder in 'text_manager_prompt_new' has been corrected to avoid conflict.

TEXTS = {
    # Key: { "description": "Arabic Label for the button", "default": "The actual text with placeholders" }
    
    # --- General UI & Actions ---
    "action_cancelled": {
        "description": "رسالة إلغاء العملية",
        "default": "✅ تم إلغاء العملية بنجاح."
    },
    "back_to_main_panel": {
        "description": "نص زر العودة للوحة الرئيسية",
        "default": "🔙 العودة إلى اللوحة الرئيسية"
    },
    
    # --- User-Facing Messages ---
    "user_welcome": {
        "description": "رسالة الترحيب بالمستخدم",
        "default": "👋 أهلًا وسهلًا بك يا #name!\nأنا هنا لخدمتك."
    },
    "user_default_reply": {
        "description": "الرد الافتراضي للمستخدم",
        "default": "✅ تم استلام رسالتك بنجاح، شكراً لتواصلك."
    },
    "user_force_subscribe": {
        "description": "رسالة طلب الاشتراك الإجباري",
        "default": "عذرًا, لاستخدام هذا البوت, يرجى الاشتراك أولاً في قناتنا."
    },

    # --- Admin Panel Titles ---
    "admin_panel_title": {
        "description": "عنوان لوحة /admin",
        "default": "🔧 **لوحة التحكم الإدارية**"
    },
    "adv_panel_title": {
        "description": "عنوان لوحة /hijri",
        "default": "🛠️ **لوحة التحكم المتقدمة (غرفة المحركات)**"
    },
    
    # --- Text Manager Feature Texts ---
    "text_manager_title": {
        "description": "عنوان قائمة مدير النصوص",
        "default": "✏️ **مدير النصوص الملكي**\n\nاختر النص الذي تريد تعديله:"
    },
    "text_manager_prompt_new": {
        "description": "رسالة طلب النص الجديد (لا تعدل هذا)",
        # --- THE FIX IS HERE ---
        "default": "النص الحالي لـ `{text_name}` هو:\n`{current_text}`\n\nأرسل الآن النص الجديد:"
    },
    "text_manager_success": {
        "description": "رسالة نجاح تحديث النص",
        "default": "✅ تم تحديث النص `{text_name}` بنجاح."
    },
}

def get_text(key: str, **kwargs) -> str:
    """
    The Smart Librarian function.
    Gets custom text, falls back to default, and formats it.
    """
    custom_texts = data_store.bot_data.get('custom_texts', {})
    default_template = TEXTS.get(key, {}).get("default", f"_{key}_")
    text_template = custom_texts.get(key, default_template)
    try:
        return text_template.format(**kwargs)
    except KeyError:
        return text_template

def get_all_text_descriptions() -> list:
    """Returns a list of (key, description) for the text manager buttons."""
    return sorted([(key, details["description"]) for key, details in TEXTS.items()])
