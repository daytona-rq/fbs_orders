import aiohttp
import asyncio
from aiogram import Bot
from aiogram.enums import ParseMode
from redis.asyncio import Redis
import json
from datetime import datetime, date

from src.telegram.bot import bot
from src.database.queries.orm import db
from src.wildberries.models import wb_client, Card

semaphore = asyncio.Semaphore(10)
redis = Redis()

async def user_report(user: tuple, session: aiohttp.ClientSession):
    async with semaphore:
        chat_id, wb_token = user[0], user[1]
        headers = {'Authorization': wb_token}
        key_redis = f'orders:{chat_id}'

        session.headers.update(headers)
        cur_orders = await wb_client.get_new_orders(session)
        for order in cur_orders:
            order_date = datetime.strptime(order['createdAt'][:10], '%Y-%m-%d').date()
            if order_date == date.today():
                order_str = json.dumps(order, sort_keys=True)
                if await redis.sismember(key_redis, order_str):
                    continue
                else:
                    card = await Card.create(session, order, chat_id)
                    report_text = await card.create_report()
                    await bot.send_message(chat_id, report_text, parse_mode=ParseMode.HTML)
                    await redis.sadd(key_redis, order_str)

async def send_orders():
    async with aiohttp.ClientSession() as session:
        active_users = await db.active_users_list()
        tasks = []

        for user in active_users:
            tasks.append(
                asyncio.create_task(user_report(user, session))
            )

        await asyncio.gather(*tasks)
