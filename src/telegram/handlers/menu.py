from aiogram import Router, F
from aiogram.types import CallbackQuery

import src.telegram.keyboards as kb


router = Router()

@router.callback_query(F.data == 'back')
async def back(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Меню', reply_markup=kb.start_menu)

@router.callback_query(F.data == 'user_settings')
async def user_info(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Что меняем?', reply_markup=kb.user_settings)



