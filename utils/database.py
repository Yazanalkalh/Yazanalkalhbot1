# ... (كل الكود السابق في الملف يبقى كما هو) ...
# ... (import statements, client connection, etc.) ...

# --- Settings Functions (from previous step) ---
def get_all_settings():
    settings_doc = settings_collection.find_one({"_id": "main_bot_config"})
    return settings_doc if settings_doc else {}

def get_setting(setting_name: str, default_value=None):
    settings_doc = settings_collection.find_one({"_id": "main_bot_config"}, {setting_name: 1})
    if settings_doc and setting_name in settings_doc:
        return settings_doc[setting_name]
    return default_value

def update_setting(setting_name: str, value):
    try:
        settings_collection.update_one(
            {"_id": "main_bot_config"},
            {"$set": {setting_name: value}},
            upsert=True
        )
    except Exception as e:
        print(f"DB SETTING UPDATE ERROR for '{setting_name}': {e}")

# --- User Functions ---
def add_user(user_id: int, full_name: str, username: str):
    """Adds or updates a user in the database."""
    users_collection.update_one(
        {"_id": user_id},
        {
            "$set": {
                "full_name": full_name,
                "username": username,
                "last_seen": datetime.datetime.utcnow()
            },
            "$setOnInsert": { # هذه الحقول تضاف فقط عند إنشاء المستخدم لأول مرة
                "is_banned": False,
                "last_message_fingerprint": None
            }
        },
        upsert=True
    )

# --- NEW FUNCTIONS REQUIRED BY message_handler ---

def is_user_banned(user_id: int) -> bool:
    """✅ دالة جديدة: تتحقق بسرعة إذا كان المستخدم محظورًا."""
    user = users_collection.find_one({"_id": user_id}, {"is_banned": 1})
    return user.get("is_banned", False) if user else False

def get_dynamic_reply(text: str) -> str or None:
    """✅ دالة جديدة: تبحث عن رد ديناميكي واحد."""
    if not text: return None
    # نفترض أن الردود الديناميكية مخزنة في مستند الإعدادات
    # Example: { "_id": "main_bot_config", "dynamic_replies": { "مرحبا": "أهلا بك" } }
    reply_data = settings_collection.find_one(
        {"_id": "main_bot_config"},
        {f"dynamic_replies.{text}": 1}
    )
    if reply_data and "dynamic_replies" in reply_data:
        return reply_data["dynamic_replies"].get(text)
    return None

def get_user_last_fingerprint(user_id: int) -> str or None:
    """✅ دالة جديدة: تجلب آخر بصمة رسالة للمستخدم."""
    user = users_collection.find_one({"_id": user_id}, {"last_message_fingerprint": 1})
    return user.get("last_message_fingerprint") if user else None

def update_user_last_fingerprint(user_id: int, fingerprint: str):
    """✅ دالة جديدة: تحدث بصمة آخر رسالة للمستخدم."""
    users_collection.update_one(
        {"_id": user_id},
        {"$set": {"last_message_fingerprint": fingerprint}}
    )

# ... (بقية الدوال في ملفك تبقى كما هي بدون تغيير) ...
