# ... (كل الكود السابق في الملف يبقى كما هو) ...

# --- NEW: Forwarded Message Link Functions ---
# نستخدم مجموعة جديدة لتخزين هذه البيانات المؤقتة
forward_links_collection = db.get_collection("ForwardLinks")

def log_forward_link(admin_message_id: int, user_id: int, original_message_id: int):
    """✅ دالة جديدة: تحفظ رابط الرسالة في قاعدة البيانات لمنع فقدانه."""
    forward_links_collection.insert_one({
        "_id": admin_message_id,
        "user_id": user_id,
        "original_message_id": original_message_id,
        "created_at": datetime.datetime.utcnow()
    })
    # يمكنك إضافة مؤشر TTL لحذف الروابط القديمة تلقائيًا بعد فترة
    # forward_links_collection.create_index("created_at", expireAfterSeconds=86400) # (e.g., 24 hours)

def get_forward_link(admin_message_id: int):
    """✅ دالة جديدة: تجلب رابط الرسالة من قاعدة البيانات."""
    return forward_links_collection.find_one({"_id": admin_message_id})

def delete_forward_link(admin_message_id: int):
    """✅ دالة جديدة: تحذف الرابط بعد استخدامه."""
    forward_links_collection.delete_one({"_id": admin_message_id})


# --- NEW: Functions to manage reminders and replies ---

def get_all_reminders() -> list:
    """✅ دالة جديدة: تجلب كل التذكيرات من الإعدادات."""
    return get_setting("reminders", [])

def delete_reminder(reminder_text: str):
    """✅ دالة جديدة: تحذف تذكيرًا معينًا بشكل آمن باستخدام $pull."""
    settings_collection.update_one(
        {"_id": "main_bot_config"},
        {"$pull": {"reminders": reminder_text}}
    )

def get_all_dynamic_replies() -> dict:
    """✅ دالة جديدة: تجلب كل الردود الديناميكية."""
    return get_setting("dynamic_replies", {})

def delete_dynamic_reply(keyword: str):
    """✅ دالة جديدة: تحذف ردًا ديناميكيًا بشكل آمن باستخدام $unset."""
    settings_collection.update_one(
        {"_id": "main_bot_config"},
        {"$unset": {f"dynamic_replies.{keyword}": ""}}
    )

# ... (بقية الدوال في ملفك تبقى كما هي بدون تغيير) ...
