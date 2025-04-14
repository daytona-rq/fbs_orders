from celery import Celery, Task
import asyncio
import logging
from src.wildberries.wb_main import send_orders

app = Celery('my_app')


class BaseTaskWithRetry(Task):
    autoretry_for = (Exception,)  # повтор при любых исключениях
    retry_kwargs = {'max_retries': 3, 'countdown': 60}  # максимум 3 повтора, раз в 60 сек
    retry_backoff = True  # экспоненциальный бэкофф (60, 120, 240 и т.д.)
    retry_jitter = True  # добавить случайную задержку, чтобы снизить нагрузку
    acks_late = True  # подтверждаем выполнение только после успеха
    default_retry_delay = 60  # на всякий случай

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logging.error(f"Задача {self.name} ({task_id}) упала: {exc}")


@app.task(name='app.tasks.send_orders_task', base=BaseTaskWithRetry, bind=True)
def send_orders_task(self):
    try:
        asyncio.run(send_orders())
    except Exception as e:
        logging.exception(f"Ошибка в send_orders: {e}")
        raise self.retry(exc=e)
