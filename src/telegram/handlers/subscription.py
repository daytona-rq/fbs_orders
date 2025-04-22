import os

from aiogram import Router, F
from aiogram.types import CallbackQuery, LabeledPrice
from aiogram.enums import ParseMode

from src.database.queries.orm import db
from src.telegram.bot import bot
import src.telegram.keyboards as kb
from src.telegram.texts import Texts
from src.database.config import settings
from src.yookassa_dir.payment import create_payment


PAYMENT_PROVIDER_TOKEN = settings.PAY_TOKEN

PRICES = [
    LabeledPrice(label='Подписка', amount=14900)
]

router = Router()

@router.callback_query(F.data == 'subscribe_status')
async def sub_status(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    sub_date = await db.check_sub_status(chat_id)
    if sub_date:
        await callback.message.edit_text(
                               text=f'Подписка активна до {sub_date}',
                               reply_markup=kb.to_menu)
    else:
        await callback.message.edit_text(
                               Texts.not_sub_txt,
                               reply_markup=kb.sub_menu)

@router.callback_query(F.data == 'buy_sub')
async def buy_sub(callback: CallbackQuery):
    await callback.answer('')
    chat_id = callback.message.chat.id
    payment_url, payment_id = create_payment(chat_id)
    await callback.message.answer(f'ID вашей операции: \n{payment_id}', 
                                  reply_markup=kb.create_payment_kb(payment_url))