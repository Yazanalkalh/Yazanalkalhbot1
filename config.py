import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
MONGO_URI = os.getenv("MONGO_URI")

if not all([API_TOKEN, ADMIN_CHAT_ID, MONGO_URI]):
    print("❌ FATAL: Missing one or more environment variables (BOT_TOKEN, ADMIN_CHAT_ID, MONGO_URI)")
    exit(1)
