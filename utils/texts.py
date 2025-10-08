import data_store

# This is the new, central "Smart Dictionary" for the bot.
# It holds all default texts and provides a function to get the customized version if it exists.

# The master dictionary of all default texts in the bot, organized by key.
TEXTS = {
    # General UI & Actions
    "action_cancelled": "✅ تم إلغاء العملية.",
    "back_to_main_panel": "🔙 العودة إلى اللوحة الرئيسية",
    "back_to_advanced_panel": "🔙 العودة للوحة المتقدمة",
    "add_more": "➕ إضافة المزيد",
    "generic_error": "❌ حدث خطأ غير متوقع: {e}",
    "invalid_number": "❌ إدخال خاطئ. الرجاء إرسال رقم صحيح.",
    "error_file_not_txt": "❌ خطأ: يجب أن يكون الملف من نوع نصي (.txt) فقط.",
    "error_not_a_file": "❌ خطأ: الرجاء إرسال ملف وليس نصًا.",

    # User-Facing Messages
    "user_welcome": "👋 أهلًا وسهلًا بك يا #name!\nأنا هنا لخدمتك.",
    "user_default_reply": "✅ تم استلام رسالتك بنجاح، شكراً لتواصلك.",
    "user_admin_command_warning": "⚠️ <b>تنبيه خاص</b> 👑\n\nهذا الأمر مخصص للمدير فقط 🔒",
    "user_maintenance_mode": "عذرًا، البوت قيد الصيانة حاليًا. سنعود قريباً.",
    "user_force_subscribe": "عذرًا, لاستخدام هذا البوت, يرجى الاشتراك أولاً في قناتنا.",
    "user_anti_duplicate": "لقد استلمت هذه الرسالة منك للتو.",
    "user_help_menu_title": "📖 **فهرس الردود التلقائية:**\n\nاختر أحد الأوامر من القائمة أدناه:",
    "user_help_not_found": "⚠️ عذرًا، لم يتم العثور على هذا الرد. قد يكون قد تم حذفه.",

    # Admin Panel (/admin) Titles
    "admin_panel_title": "🔧 **لوحة التحكم الإدارية**",
    "dyn_replies_menu_title": "📝 **الردود الديناميكية**\n\nاختر الإجراء:",
    "reminders_menu_title": "💭 **إدارة التذكيرات**\n\nاختر الإجراء:",
    # ... (add all other menu titles from panel.py)

    # Admin Panel - FSM Prompts
    "prompt_dyn_reply_keyword": "📝 أرسل **الكلمة المفتاحية**:",
    "prompt_dyn_reply_content": "👍 الآن أرسل **المحتوى** للرد.",
    "prompt_dyn_reply_delete": "🗑️ أرسل الكلمة المفتاحية للحذف:",
    "prompt_import_replies": "📥 أرسل ملف الردود (.txt) بالتنسيق: `keyword|reply`",
    "prompt_new_reminder": "💭 أرسل نص التذكير:",
    "prompt_delete_reminder": "🗑️ أرسل رقم التذكير للحذف:",
    "prompt_import_reminders": "📥 أرسل ملف التذكيرات (.txt)، كل تذكير في سطر.",
    # ... (add all other prompts from panel.py)

    # Admin Panel - FSM Success/Error Replies
    "success_dyn_reply_added": "✅ **تمت برمجة الرد بنجاح!**",
    "success_dyn_reply_deleted": "✅ تم حذف الرد الخاص بـ `{keyword}`",
    "error_dyn_reply_not_found": "❌ لم يتم العثور على رد بهذا المفتاح.",
    "success_import_replies": "✅ **اكتمل استيراد الردود!**\n- ناجحة: {success}\n- فاشلة: {fail}",
    "success_reminder_added": "✅ **تمت إضافة التذكير بنجاح!**",
    "success_reminder_deleted": "✅ تم حذف التذكير:\n`{removed}`",
    "error_invalid_index": "❌ رقم غير صالح. (1 - {max_len})",
    "success_import_reminders": "✅ **اكتمل استيراد التذكيرات!**\n- تم استيراد {count} تذكيرًا بنجاح.",
    
    # Advanced Panel (/hijri)
    "adv_panel_title": "🛠️ **لوحة التحكم المتقدمة (غرفة المحركات)**",
    "adv_toggle_success": "✅ تم {status} ميزة '{feature_name}'.",
    "adv_text_manager_menu": "✏️ **إدارة نصوص البوت**",
    
    # Text Manager Feature
    "text_manager_title": "✏️ **مدير النصوص الملكي**\n\nاختر النص الذي تريد تعديله:",
    "text_manager_prompt_new": "النص الحالي لـ `{key}` هو:\n`{current_text}`\n\nأرسل الآن النص الجديد:",
    "text_manager_success": "✅ تم تحديث النص `{key}` بنجاح.",
}

def get_text(key: str, **kwargs) -> str:
    """
    The Smart Librarian function.
    It gets custom text from the DB, falls back to default, and formats it.
    """
    # 1. Look in the "special notes" (database) first.
    custom_texts = data_store.bot_data.get('custom_texts', {})
    
    # 2. If not found, get it from the "original book" (default dictionary).
    text_template = custom_texts.get(key, TEXTS.get(key, f"_{key}_"))
    
    # 3. Use .format() to dynamically insert any provided values (like names, numbers, etc.)
    try:
        return text_template.format(**kwargs)
    except KeyError:
        # If the format key is missing (e.g., forgot to provide {keyword}), return the raw template
        return text_template

def get_all_text_keys() -> list:
    """Returns a list of all editable text keys, sorted."""
    return sorted(TEXTS.keys())
