import os
from dotenv import load_dotenv

# For local development, it loads variables from a .env file
load_dotenv()

print("🔍 Checking environment variables...")

# Required environment variables
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID_STR = os.getenv("ADMIN_CHAT_ID")
MONGO_URI = os.getenv("MONGO_URI")

# Optional environment variables
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Validate that essential variables exist
if not all([API_TOKEN, ADMIN_CHAT_ID_STR, MONGO_URI]):
    print("❌ Error: Make sure BOT_TOKEN, ADMIN_CHAT_ID, and MONGO_URI are set in your environment!")
    exit(1)

# Validate and convert ADMIN_CHAT_ID to an integer
try:
    ADMIN_CHAT_ID = int(ADMIN_CHAT_ID_STR)
    print(f"✅ Admin ID has been set: {ADMIN_CHAT_ID}")
except ValueError:
    print("❌ Error: ADMIN_CHAT_ID must be a valid integer.")
    exit(1)

print("✅ All essential environment variables are present.")


