from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal

class YooKassaPaymentAmount(BaseModel):
    value: str = Field(..., pattern=r"^\d+\.\d{2}$")  # Формат "100.00"
    currency: str = Field(default="RUB", pattern="^[A-Z]{3}$")

class YooKassaPaymentMethod(BaseModel):
    type: str  # "bank_card", "yoo_money"
    id: str

class YooKassaWebhookObject(BaseModel):
    id: str
    status: Literal["pending", "waiting_for_capture", "succeeded", "canceled"]
    amount: YooKassaPaymentAmount
    payment_method: Optional[YooKassaPaymentMethod] = None
    metadata: dict  # Обязательное поле

    @field_validator('metadata')
    @classmethod
    def check_chat_id(cls, v: dict) -> dict:
        if "chat_id" not in v:
            raise ValueError("metadata must contain 'chat_id'")
        if not isinstance(v["chat_id"], int):
            raise ValueError("chat_id must be integer")
        return v

class YooKassaWebhook(BaseModel):
    type: Literal[
        "payment.waiting_for_capture",
        "payment.succeeded",
        "payment.canceled",
        "refund.succeeded"
    ]
    event: str  # Для обратной совместимости
    object: YooKassaWebhookObject