from utils import database

TEXTS = {
    # ... (لا تغييرات هنا، محتوى القاموس سليم) ...
    # --- General UI & Actions ---
    "action_cancelled": {
        "description": "رسالة إلغاء العملية",
        "default": "✅ تم إلغاء العملية بنجاح."
    },
    # ... (rest of the dictionary)
}

# ✅ تم الإصلاح: عادت الدالة لتكون متزامنة
def get_text(key: str, **kwargs) -> str:
    # لم نعد بحاجة لـ await هنا
    custom_texts = database.get_setting('custom_texts', {})
    default_template = TEXTS.get(key, {}).get("default", f"_{key}_")
    text_template = custom_texts.get(key, default_template) if custom_texts else default_template
    try:
        return text_template.format(**kwargs)
    except KeyError:
        return text_template

def get_all_text_descriptions() -> list:
    return sorted([(key, details["description"]) for key, details in TEXTS.items()])
