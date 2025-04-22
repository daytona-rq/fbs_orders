import json
from fastapi import APIRouter, Request, HTTPException, Header, Response
from fastapi.responses import JSONResponse
from .schemas import YooKassaWebhook
import hmac
import hashlib
import os
import logging

from yookassa.domain.notification import WebhookNotification
from src.telegram.bot import bot
from src.database.database import async_session_maker
from src.database.config import settings
from src.database.queries.orm import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/yookassa", tags=["Webhooks"])

YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

async def send_telegram_notification(chat_id: int, message: str):
    """Отправка сообщения через Telegram Bot API"""
    bot.send_message(chat_id, message)

async def process_payment(payment_data):
    """Обработка успешного платежа"""
    try:
        chat_id = payment_data.metadata["chat_id"]
        amount = payment_data.amount.value
        
        # 1. Обновляем данные в БД (пример)
        async with async_session_maker() as db:
            # Ваша логика обновления подписки/баланса
            pass
            
        # 2. Отправляем уведомление
        message = (
            f"✅ Платеж на {amount} руб. успешно завершен!\n"
            f"ID платежа: <code>{payment_data.id}</code>"
        )
        await send_telegram_notification(chat_id, message)
        
    except KeyError:
        print("Ошибка: chat_id не найден в metadata")
    except Exception as e:
        print(f"Ошибка обработки платежа: {e}")

@router.post("/webhook")
async def webhook_handler(request: Request):
    event_json = await request.json()
    payment_status = event_json['event']
    chat_id = event_json['object']['metadata']['chat_id']
    if payment_status == 'payment.succeeded':
        await db.subscribe(chat_id)
        await bot.send_message(chat_id, text='Ауе подписка оформлена 💋')
    if payment_status == 'payment.canceled':
        await bot.send_message(chat_id, text='Платеж был отменён')
    return JSONResponse(content={"status": "success"}, status_code=200)
