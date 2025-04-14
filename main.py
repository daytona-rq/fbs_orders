import asyncio
import logging
from aiogram import Dispatcher
from aiohttp import ClientSession

from src.telegram.bot import bot
from src.telegram.handlers import setup_routers
from src.database.queries.orm import db
from src.wildberries.models import wb_client
from src.wildberries.wb_main import send_orders

dp = Dispatcher()

headers = {'Authorization': 'eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwMjE3djEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc1Njg3ODYzNiwiaWQiOiIwMTk1NjI0Ny1mMTE5LTc2OGYtYTJhNy1hMDJkZjRiOGMxNjMiLCJpaWQiOjEyMDUzNTk5Mywib2lkIjoxMzM2OTcyLCJzIjozMzI2LCJzaWQiOiJlZTc4Nzg1OC01MTdhLTRjOTQtYWNhNy03NjBjYWNkNGNkMTIiLCJ0IjpmYWxzZSwidWlkIjoxMjA1MzU5OTN9.d98ix-WC5jrftdCE9L3hL_ztQ1YFUsCnYz2mndnizfsCkkjGVDR050P-UiUQacv3QDfAkFl5uksJ1aI6nOONeA'}

async def main():
    await db.create_tables()
    dp.include_router(setup_routers())
    await send_orders()
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Session closed')