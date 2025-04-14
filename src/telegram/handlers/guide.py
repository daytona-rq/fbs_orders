from aiogram import Router, F
from aiogram.types import CallbackQuery

import src.telegram.keyboards as kb


router = Router()

@router.callback_query(F.data == 'guide')
async def help_but(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('<Раздел помощь>', reply_markup=kb.help_kb)

@router.callback_query(F.data == 'text_guide')
async def text_guide(callback: CallbackQuery):
    await callback.answer('Текстовый гайд')