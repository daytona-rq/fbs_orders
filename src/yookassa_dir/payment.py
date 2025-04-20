import uuid

from yookassa import Configuration, Payment

from src.database.config import settings

Configuration.configure(account_id=settings.SHOP_ID, 
                        secret_key=settings.YOOKASSA_SECRET_KEY)

def create_payment(chat_id: int):
    payment = Payment.create({
        "amount": {
            "value": "149.00",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/kailas_order_bot"
        },
        "capture": True,
        "description": "Подписка на бота",
        "metadata": {
            "chat_id": chat_id
        }
    }, uuid.uuid4())

    return payment.confirmation.confirmation_url, payment.id
