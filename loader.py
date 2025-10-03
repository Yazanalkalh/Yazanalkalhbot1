from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import BOT_TOKEN

# تهيئة مخزن الحالات في الذاكرة
storage = MemoryStorage()

# إنشاء كائن البوت
bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")

# إنشاء كائن المرسل (Dispatcher)
dp = Dispatcher(bot, storage=storage)
