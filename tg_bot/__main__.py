from aiogram import Bot, Dispatcher
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import TOKEN
from controller__init import Controller


async def on_startup(_):
    scheduler.start()
    await Controller.clean_rooms()


async def on_shutdown(_):
    pass


scheduler = AsyncIOScheduler()
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)
dp.setup_middleware(LoggingMiddleware())
