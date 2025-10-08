import data_store

# This is the new, central "Smart Dictionary" for the bot.
# It now includes a user-friendly Arabic description for each text key.

TEXTS = {
    # Key: { "description": "Arabic Label for the button", "default": "The actual text" }
    
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
        "description": "رسالة الترحيب بالمستخدم الجديد",
        "default": "👋 أهلًا وسهلًا بك يا #name!\nأنا هنا لخدمتك."
    },
    "user_default_reply": {
        "description": "الرد الافتراضي للمستخدم",
        "default": "✅ تم استلام رسالتك بنجاح، شكراً لتواصلك."
    },
    "user_admin_command_warning": {
        "description": "رسالة التحذير عند استخدام أمر للمدير",
        "default": "⚠️ <b>تنبيه خاص</b> 👑\n\nهذا الأمر مخصص للمدير فقط 🔒"
    },
    "user_maintenance_mode": {
        "description": "رسالة وضع الصيانة للمستخدم",
        "default": "عذرًا، البوت قيد الصيانة حاليًا. سنعود قريباً."
    },
    "user_force_subscribe": {
        "description": "رسالة طلب الاشتراك الإجباري",
        "default": "عذرًا, لاستخدام هذا البوت, يرجى الاشتراك أولاً في قناتنا."
    },

    # --- Admin Panel Titles & Prompts ---
    "admin_panel_title": {
        "description": "عنوان لوحة تحكم المدير (/admin)",
        "default": "🔧 **لوحة التحكم الإدارية**"
    },
    "adv_panel_title": {
        "description": "عنوان لوحة التحكم المتقدمة (/hijri)",
        "default": "🛠️ **لوحة التحكم المتقدمة (غرفة المحركات)**"
    },
    "prompt_dyn_reply_keyword": {
        "description": "رسالة طلب الكلمة المفتاحية للرد",
        "default": "📝 أرسل **الكلمة المفتاحية**:"
    },
    "prompt_dyn_reply_content": {
        "description": "رسالة طلب محتوى الرد",
        "default": "👍 الآن أرسل **المحتوى** للرد."
    },
    "success_dyn_reply_added": {
        "description": "رسالة نجاح إضافة رد",
        "default": "✅ **تمت برمجة الرد بنجاح!**"
    },
    # ... You can add every single text from the bot here for full control ...

    # --- Text Manager Feature Texts ---
    "text_manager_title": {
        "description": "عنوان قائمة مدير النصوص",
        "default": "✏️ **مدير النصوص الملكي**\n\nاختر النص الذي تريد تعديله:"
    },
    "text_manager_prompt_new": {
        "description": "رسالة طلب النص الجديد",
        "default": "النص الحالي لـ `{key}` هو:\n`{current_text}`\n\nأرسل الآن النص الجديد:"
    },
    "text_manager_success": {
        "description": "رسالة نجاح تحديث النص",
        "default": "✅ تم تحديث النص `{key}` بنجاح."
    },
}

def get_text(key: str, **kwargs) -> str:
    """
    The Smart Librarian function.
    It gets custom text from the DB, falls back to default, and formats it.
    """
    custom_texts = data_store.bot_data.get('custom_texts', {})
    
    # Get the default text template from the new structure
    default_template = TEXTS.get(key, {}).get("default", f"_{key}_")
    
    # Get the custom text if it exists, otherwise use the default
    text_template = custom_texts.get(key, default_template)
    
    try:
        return text_template.format(**kwargs)
    except KeyError:
        return text_template

def get_all_text_descriptions() -> list:
    """
    Returns a list of tuples (key, description) for all editable texts.
    This is used to build the beautiful buttons for the admin.
    """
    return sorted([(key, details["description"]) for key, details in TEXTS.items()])
