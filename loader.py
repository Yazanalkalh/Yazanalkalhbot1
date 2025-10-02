from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import API_TOKEN

# Initialize storage for FSM states in memory
storage = MemoryStorage()

# Initialize the Bot instance with the API token
bot = Bot(token=API_TOKEN)

# Initialize the Dispatcher instance
dp = Dispatcher(bot, storage=storage)


