from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import API_TOKEN

# Using MemoryStorage for FSM states. It's simple and reliable for most cases.
storage = MemoryStorage()

# Initialize the bot with HTML parsing mode.
bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=storage)
