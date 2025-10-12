import os

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
MONGO_URI = os.getenv("MONGO_URI")

if not all([API_TOKEN, ADMIN_CHAT_ID, MONGO_URI]):
    print("❌ FATAL ERROR: BOT_TOKEN, ADMIN_CHAT_ID, or MONGO_URI not found in environment variables!")
    exit(1)
