import os

# This function reads the environment variable, cleans it, and converts it to an integer.
# This prevents errors from invisible spaces or wrong types.
def get_env_var_as_int(name):
    var = os.getenv(name)
    if var is None or not var.strip():
        return None
    try:
        return int(var.strip())
    except (ValueError, TypeError):
        return None

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = get_env_var_as_int("ADMIN_CHAT_ID")
MONGO_URI = os.getenv("MONGO_URI")

# This check is crucial. It stops the bot if any essential variable is missing.
if not all([API_TOKEN, ADMIN_CHAT_ID, MONGO_URI]):
    print("❌ FATAL ERROR: BOT_TOKEN, ADMIN_CHAT_ID, or MONGO_URI is missing or invalid in environment variables!")
    exit(1)
