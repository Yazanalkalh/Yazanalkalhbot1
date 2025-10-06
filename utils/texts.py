import data_store

# This is the new, central "Smart Dictionary" for the bot.
# It holds all default texts and provides a function to get the customized version if it exists.

# The master dictionary of all default texts in the bot, organized by category.
# Each text has a unique key (e.g., 'admin_panel_title').
TEXTS = {
    # General
    "action_cancelled": "✅ تم إلغاء العملية بنجاح.",
    "back_to_main_panel": "🔙 العودة إلى اللوحة الرئيسية",
    "back_to_advanced_panel": "🔙 العودة للوحة المتقدمة",
    "add_more": "➕ إضافة المزيد",
    "generic_error": "❌ حدث خطأ غير متوقع: {e}",
    "invalid_number": "❌ إدخال خاطئ. الرجاء إرسال رقم صحيح.",

    # User-facing texts
    "user_welcome": "👋 أهلًا وسهلًا بك يا #name!\nأنا هنا لخدمتك.",
    "user_default_reply": "✅ تم استلام رسالتك بنجاح، شكراً لتواصلك.",
    "user_admin_command_warning": "⚠️ <b>تنبيه خاص</b> 👑\n\nهذا الأمر مخصص للمدير فقط 🔒",
    "user_maintenance_mode": "عذرًا، البوت قيد الصيانة حاليًا. سنعود قريباً.",
    "user_force_subscribe": "عذرًا, لاستخدام هذا البوت, يرجى الاشتراك أولاً في قناتنا.",
    "user_anti_duplicate": "لقد استلمت هذه الرسالة منك للتو.",
    "user_help_menu_title": "📖 **فهرس الردود التلقائية:**\n\nاختر أحد الأوامر من القائمة أدناه:",
    "user_help_not_found": "⚠️ عذرًا، لم يتم العثور على هذا الرد. قد يكون قد تم حذفه.",

    # Admin Panel (/admin)
    "admin_panel_title": "🔧 **لوحة التحكم الإدارية**",
    "admin_reply_sent": "✅ **تم إرسال الرد بنجاح.**",
    "admin_reply_fail": "❌ **فشل إرسال الرد:** {e}",

    # Admin Panel - FSM Prompts & Replies
    "prompt_dyn_reply_keyword": "📝 أرسل **الكلمة المفتاحية**:",
    "prompt_dyn_reply_content": "👍 الآن أرسل **المحتوى** للرد.",
    "success_dyn_reply_added": "✅ **تمت برمجة الرد بنجاح!**",
    "prompt_dyn_reply_delete": "🗑️ أرسل الكلمة المفتاحية للحذف:",
    "success_dyn_reply_deleted": "✅ تم حذف الرد الخاص بـ `{keyword}`",
    "error_dyn_reply_not_found": "❌ لم يتم العثور على رد بهذا المفتاح.",
    "prompt_import_replies": "📥 أرسل الملف النصي (.txt) الخاص بالردود:",
    "success_import_replies": "✅ **اكتمل استيراد الردود!**\n- ناجحة: {success}\n- فاشلة: {fail}",
    "error_file_not_txt": "❌ خطأ: يجب أن يكون الملف من نوع نصي (.txt) فقط.",
    "error_not_a_file": "❌ خطأ: الرجاء إرسال ملف وليس نصًا.",
    # ... (You can add all other prompts and success/error messages from fsm_handlers.py here)

    # Advanced Panel (/hijri)
    "adv_panel_title": "🛠️ **لوحة التحكم المتقدمة (غرفة المحركات)**",
    "adv_toggle_success": "✅ تم {status} ميزة '{feature_name}'.",
    "adv_maintenance_on": "🔴 إيقاف البوت (تفعيل الصيانة)",
    "adv_maintenance_off": "🟢 تشغيل البوت (إيقاف الصيانة)",
    # ... (and all other texts from advanced_panel.py)
    
    # Text Customization Feature
    "text_manager_title": "✏️ **إدارة نصوص البوت**\n\nاختر النص الذي تريد تعديله:",
    "text_manager_prompt_new": "النص الحالي هو:\n`{current_text}`\n\nأرسل الآن النص الجديد:",
    "text_manager_success": "✅ تم تحديث النص بنجاح.",
}

def get_text(key: str) -> str:
    """
    The Smart Librarian function.
    It first looks for a custom text in the database (data_store).
    If not found, it falls back to the default text from the TEXTS dictionary.
    """
    # 1. Look in the "special notes" (database) first.
    custom_texts = data_store.bot_data.get('custom_texts', {})
    if key in custom_texts:
        return custom_texts[key]
    
    # 2. If not found, get it from the "original book" (default dictionary).
    return TEXTS.get(key, f"_{key}_") # Return _key_ if text is missing, for easy debugging

def get_all_text_keys() -> list:
    """Returns a list of all editable text keys, sorted."""
    return sorted(TEXTS.keys())
