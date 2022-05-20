from aiogram import Bot, Dispatcher
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import TOKEN


async def on_startup(_):
    pass


async def on_shutdown(_):
    pass


bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)
dp.setup_middleware(LoggingMiddleware())
