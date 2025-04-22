import aiohttp
import asyncio
import json
from datetime import date, timedelta
from aiogram.enums import ParseMode

from src.telegram.bot import bot
from src.database.queries.orm import db
from src.wildberries.models import wb_client, Card
from src.redis import redis

semaphore = asyncio.Semaphore(10)

DAILY_STATS_FIELDS = {
    'daily_count': ("Всего заказов", ''),
    'daily_total': ("Сумма выручки", '₽'),
    'daily_selfcost': ("Сумма себестоимостей", '₽'),
    'daily_commission': ("Общая комиссия Wildberries", '₽'),
    'daily_logistic_cost': ("Общая стоимость логистики", '₽'),
    'daily_cost_tax': ("Общая сумма налога", '₽'),
    'daily_profit': ("Общая прибыль", '₽'),
}

async def yesterday():
    return date.today() - timedelta(days=1)

async def daily_report(chat_id: int) -> str:
    date = (await yesterday()).isoformat()
    stats_key = f"user_stats:{chat_id}:{date}"

    pipe = redis.pipeline()
    for field in DAILY_STATS_FIELDS:
        pipe.hget(stats_key, field)
    values = await pipe.execute()

    stats_dict = dict(zip(DAILY_STATS_FIELDS.keys(), values))

    report_lines = [f"Отчёт за {date.today()}:"]
    for key, (label, suffix) in DAILY_STATS_FIELDS.items():
        val = stats_dict.get(key) or '0'
        report_lines.append(f"{label}: {val}{suffix}")

    await redis.delete(stats_key)

    return "\n".join(report_lines)

async def collect_stats(chat_id: int, card: Card) -> None:
    date = (await yesterday()).isoformat()
    stats_key = f"user_stats:{chat_id}:{date}"

    updates = {
        'daily_count': 1,
        'daily_total': card.price_before_spp,
        'daily_selfcost': card.selfcost,
        'daily_cost_tax': card.cost_tax,
        'daily_logistic_cost': card.logistic_cost,
        'daily_profit': card.profit,
        'daily_commission': card.wb_commission,
    }

    pipe = redis.pipeline()
    for key, value in updates.items():
        if isinstance(value, int):
            pipe.hincrby(stats_key, key, value)
        else:
            pipe.hincrbyfloat(stats_key, key, value)
    await pipe.execute()

async def reset_daily_stats(chat_id: int) -> None:
    """Удаляет все поля статистики пользователя за указанную дату (по умолчанию — сегодня)."""
    date = (await yesterday()).isoformat()
    stats_key = f"user_stats:{chat_id}:{date}"
    await redis.delete(stats_key)

async def user_report(user: tuple[int, str]):
    async with semaphore:
        chat_id, wb_token = user
        key_redis = f'orders:{chat_id}'
        headers = {'Authorization': wb_token}
        today = date.today().isoformat()

        async with aiohttp.ClientSession(headers=headers) as session:
            cur_orders = await wb_client.get_new_orders(session)
            for order in cur_orders:
                order_date = order['createdAt'][:10]
                if order_date == today:
                    order_str = json.dumps(order, sort_keys=True)
                    if not await redis.sismember(key_redis, order_str):
                        card = await Card.create(session, order, chat_id)
                        report_text = await card.create_report(chat_id)
                        await bot.send_message(chat_id, report_text, parse_mode=ParseMode.HTML)

                        await redis.sadd(key_redis, order_str)
                        await collect_stats(chat_id, card)

#Задачи

async def send_daily_user_stats():
    active_users = await db.sub_users_list()
    for user in active_users:
        chat_id = user[0]
        report = await daily_report(chat_id)
        await bot.send_message(chat_id, text=report)


async def send_orders():
    try:
        active_users = await db.sub_users_list()
        tasks = [asyncio.create_task(user_report(user)) for user in active_users]
        await asyncio.gather(*tasks)
    except Exception as e:
        print(f"Критическая ошибка в send_orders: {e}")
    finally:
        await redis.close()
