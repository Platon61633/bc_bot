import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from db import db
from registration import setup_registration_handlers
from anons import setup_anons_handlers

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

async def main():
    setup_registration_handlers(dp, bot)
    setup_anons_handlers(dp, bot)

    await db.create_pool()
    await db.init_db()
    await dp.start_polling(bot)

if __name__ == "__main__": 
    asyncio.run(main())