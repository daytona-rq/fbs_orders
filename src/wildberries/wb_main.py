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
from src.wildberries.redis import redis

semaphore = asyncio.Semaphore(10)

async def user_report(user: tuple, session: aiohttp.ClientSession):
    async with semaphore:
        chat_id, wb_token = user[0], user[1]
        headers = {'Authorization': wb_token}
        key_redis = f'orders:{chat_id}'
        today = date.today().isoformat()

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
                    report_text = await card.create_report(chat_id)
                    await bot.send_message(chat_id, report_text, parse_mode=ParseMode.HTML)
                    await redis.sadd(key_redis, order_str)

                    #Хранение статистики за день
                    await redis.incrbyfloat(f"user:{chat_id}:daily_total:{today}", card.price_before_spp)
                    await redis.incr(f"user:{chat_id}:daily_count:{today}")
                    await redis.incrbyfloat(f"user:{chat_id}:daily_selfcost:{today}", card.selfcost)
                    await redis.incrbyfloat(f"user:{chat_id}:daily_cost_tax:{today}", card.cost_tax)
                    await redis.incrbyfloat(f"user:{chat_id}:daily_logistic_cost:{today}", card.logistic_cost)
                    await redis.incrbyfloat(f"user:{chat_id}:daily_profit:{today}", card.profit)
                    await redis.incrbyfloat(f"user:{chat_id}:daily_wb_commission:{today}", card.wb_commission)

async def send_orders():
    async with aiohttp.ClientSession() as session:
        active_users = await db.active_users_list()
        tasks = []

        for user in active_users:
            tasks.append(
                asyncio.create_task(user_report(user, session))
            )

        await asyncio.gather(*tasks)
