import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from db import db
from registration import setup_registration_handlers


logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def main():
    setup_registration_handlers(dp)
    await db.create_pool()
    await db.init_db()
    await dp.start_polling(bot)
    print('================================================++++')

if __name__ == "__main__": 
    asyncio.run(main())