from celery import Celery, Task
from celery.schedules import crontab
import logging
import asyncio
from src.wildberries.wb_main import send_orders

# Настройка Celery
app = Celery('my_app', broker='redis://localhost:6379/0')

# Логирование
logging.basicConfig(level=logging.INFO)

# Базовый класс для задач с автоповторами
class BaseTaskWithRetry(Task):
    autoretry_for = (Exception,)  # Повторить при любых исключениях
    retry_kwargs = {'max_retries': 3, 'countdown': 60}  # Максимум 3 повтора, раз в 60 секунд
    retry_backoff = True  # Экспоненциальный бэкофф (60, 120, 240 и т.д.)
    retry_jitter = True  # Добавить случайную задержку, чтобы снизить нагрузку
    acks_late = True  # Подтверждаем выполнение только после успешного завершения задачи
    default_retry_delay = 60  # Задержка по умолчанию

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logging.error(f"Задача {self.name} ({task_id}) упала: {exc}")

@app.task(name='app.tasks.send_orders_task', base=BaseTaskWithRetry, bind=True)
def send_orders_task(self):
    try:
        # Используем asyncio.run для асинхронной функции
        asyncio.run(send_orders())
    except Exception as e:
        logging.exception(f"Ошибка в send_orders: {e}")
        raise self.retry(exc=e)

# Периодическое задание, которое будет выполняться каждые 5 минут
app.conf.beat_schedule = {
    'send-orders-every-5-minutes': {
        'task': 'app.tasks.send_orders_task',
        'schedule': crontab(minute='*/5'),  # Каждые 5 минут
    },
}

# Для запуска Celery Beat и Celery Worker в командной строке:
# Запускайте worker:
# celery -A src.celery.scheduler worker --loglevel=info
# Запускайте beat:
# celery -A your_module_name beat --loglevel=info
