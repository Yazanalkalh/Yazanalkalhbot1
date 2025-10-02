from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import API_TOKEN

# تهيئة المخزن المؤقت للحالات
storage = MemoryStorage()

# إنشاء كائن البوت والمرسل (Dispatcher)
bot = Bot(token=API_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot, storage=storage)

print("✅ تم تهيئة البوت والمرسل بنجاح.")
