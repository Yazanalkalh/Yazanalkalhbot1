import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from aiogram.utils import executor
from loader import dp
from handlers import register_all_handlers
import data_store
from utils.background_tasks import startup_tasks
from web_server import start_web_server_thread

async def on_startup(dispatcher):
    data_store.initialize_data()
    register_all_handlers(dispatcher)
    await startup_tasks(dispatcher)
    print("Bot is up and running!")

if __name__ == '__main__':
    start_web_server_thread()
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
