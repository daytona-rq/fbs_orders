from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.exc import IntegrityError

import src.telegram.keyboards as kb
from src.telegram.sign_up import Reg
from src.database.queries.orm import db


router = Router()

@router.callback_query(F.data == 'trial')
async def trial(callback: CallbackQuery):
    if await db.check_trial(callback.message.chat.id):
        await callback.message.edit_text(text='Активировать пробный период?', reply_markup=kb.trial_kb)
    else:
        await callback.answer('')
        await callback.message.answer('Пробный период уже был использован')

@router.callback_query(F.data == 'activate_trial')
async def activate_trial(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    if await db.check_trial(chat_id):
        date_to = await db.base_activate_trial(chat_id)
        await callback.message.edit_text(f'Пробный период активирован до {date_to.strftime("%d.%m.%Y %H:%M")}', reply_markup=kb.sub_menu)
    else:
        await callback.answer('Пробный период уже был использован')