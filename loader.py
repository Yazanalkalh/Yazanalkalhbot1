from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import BOT_TOKEN

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN, parse_mode="HTML") # Using HTML for better formatting
dp = Dispatcher(bot, storage=storage)
