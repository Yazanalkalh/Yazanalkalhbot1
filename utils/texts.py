from utils import database

# The master dictionary of all user-facing text.
# This makes translation and customization easy.
TEXTS = {
    "action_cancelled": "✅ تم إلغاء العملية بنجاح.",
    "user_welcome": "👋 أهلًا وسهلًا بك يا {name}!\nأنا هنا لخدمتك.",
    "user_default_reply": "✅ تم استلام رسالتك بنجاح، شكراً لتواصلك.",
    "user_maintenance_mode": "عذراً، البوت قيد الصيانة حالياً. سنعود قريباً.",
    "admin_panel_title": "🔧 **لوحة التحكم الإدارية**",
    "adv_panel_title": "🛠️ **لوحة التحكم المتقدمة**",
    "text_manager_title": "✏️ **مدير النصوص**\n\nاختر النص الذي تريد تعديله:",
    "prompt_new_text": "النص الحالي هو:\n`{current_text}`\n\nأرسل الآن النص الجديد:",
    "text_update_success": "✅ تم تحديث النص `{key}` بنجاح.",
    "admin_reply_sent": "✅ تم إرسال ردك للمستخدم.",
    "admin_reply_fail": "⚠️ فشل إرسال الرد. السبب: {e}",
    "user_is_banned": "🚫 أنت محظور من استخدام هذا البوت.",
    "broadcast_prompt": "📤 أرسل الآن الرسالة التي تريد بثها للجميع (نص، صورة، الخ).",
    "broadcast_confirm": "أنت على وشك إرسال هذه الرسالة إلى {count} مستخدم. هل أنت متأكد؟",
    "broadcast_started": "✅ بدأت عملية النشر للجميع. قد تستغرق بعض الوقت...",
    "broadcast_complete": "✅ اكتمل النشر!\n\n- **النجاح:** {success}\n- **الفشل:** {fail}",
}

def get_text(key, **kwargs):
    """
    Gets text from the database if customized, otherwise from the default dictionary.
    Then, it formats the text with any provided arguments.
    """
    default_text = TEXTS.get(key, f"_{key}_") # Fallback to key name if not found
    # Get the customized text from DB, or use the default if not set.
    text_template = database.get_setting(f"custom_texts.{key}", default_text)
    
    try:
        return text_template.format(**kwargs)
    except KeyError:
        # Return the template as-is if formatting fails (e.g., missing placeholder)
        return text_template

def get_all_text_keys():
    """Returns a sorted list of all manageable text keys."""
    return sorted(TEXTS.keys())
