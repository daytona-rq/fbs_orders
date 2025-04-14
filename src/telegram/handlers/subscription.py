from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.database.queries.orm import db
from src.telegram.bot import bot
import src.telegram.keyboards as kb
from src.telegram.texts import Texts

router = Router()

@router.callback_query(F.data == 'subscribe')
async def sub_status(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    sub_date = await db.check_sub_status(chat_id)
    if sub_date:
        await bot.send_message(chat_id,
                               text=f'Подписка активна до {sub_date}')
    else:
        await bot.send_message(chat_id,
                               Texts.not_sub_txt,
                               reply_markup=kb.sub_menu)

