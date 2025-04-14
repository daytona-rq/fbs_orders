from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

import src.telegram.keyboards as kb
from src.database.queries.orm import db

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    chat_id = message.chat.id
    if not await db.user_in_db(chat_id):
        await db.add_user(chat_id)

    await message.answer('Меню', reply_markup=kb.start_menu)