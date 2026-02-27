import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.handlers import router
from app.db import Mongo
from app.middlewares import DbMiddleware
from config import BOT_TOKEN, MONGO_URI, MONGO_DB
import db_adder

async def main():
    db_adder.seed_lessons(MONGO_URI, "pilot_training", db_adder.lessons_data)
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    mongo = Mongo(uri=MONGO_URI, db_name=MONGO_DB)
    await mongo.connect()

    dp.update.middleware(DbMiddleware(mongo))
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await mongo.close()

if __name__ == "__main__":
    asyncio.run(main())
