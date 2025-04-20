from celery import Celery, Task
from celery.schedules import crontab
import logging
import asyncio

from src.telegram.bot import bot
from src.celery.tasks import send_orders, send_daily_user_stats

app = Celery('my_app', broker='redis://localhost:6379/0')

app.conf.update(
    worker_pool = 'solo'
)


logging.basicConfig(level=logging.INFO)

class BaseTaskWithRetry(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60} 
    retry_backoff = True
    retry_jitter = True  
    acks_late = True 
    default_retry_delay = 60 

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logging.error(f"Задача {self.name} ({task_id}) упала: {exc}")

@app.task(name='app.tasks.send_orders_task', base=BaseTaskWithRetry, bind=True)
def send_orders_task(self):
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_orders())
    except Exception as e:
        logging.exception(f"Ошибка в send_orders: {e}")
        raise self.retry(exc=e)

@app.task(name='app.tasks.send_daily_user_stats_task', base=BaseTaskWithRetry, bind=True)
def send_daily_user_stats_task(self):
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_daily_user_stats())
    except Exception as e:
        logging.exception(f"Ошибка в send_daily_user_stats: {e}")
        raise self.retry(exc=e)

app.conf.beat_schedule = {
    'send-orders-every-5-minutes': {
        'task': 'app.tasks.send_orders_task',
        'schedule': crontab(minute='*/5'),
    },
    'send-daily-user-stats-at-00-00': {
    'task': 'app.tasks.send_daily_user_stats_task',
    'schedule': crontab(hour=0, minute=0),
    },
}

# Для запуска Celery Beat и Celery Worker в командной строке:
# Запускайте worker:
# celery -A src.celery.scheduler worker --loglevel=info
# Запускайте beat:
# celery -A your_module_name beat --loglevel=info
