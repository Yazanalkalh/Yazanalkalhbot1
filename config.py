import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
MONGO_URI = os.getenv("MONGO_URI")

print("🔍 Checking environment variables...")
if not all([BOT_TOKEN, ADMIN_CHAT_ID, MONGO_URI]):
    print("❌ Critical Error: BOT_TOKEN, ADMIN_CHAT_ID, and MONGO_URI must be set!")
    exit(1)

try:
    ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)
    print(f"✅ Admin ID has been set: {ADMIN_CHAT_ID}")
except ValueError:
    print("❌ Critical Error: ADMIN_CHAT_ID must be a valid integer.")
    exit(1)
