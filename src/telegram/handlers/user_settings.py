from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.database.queries.orm import db
from src.telegram.keyboards import to_menu
from src.wildberries.upd_articles import update_user_article

class upd_token(StatesGroup):
    wb_token_state = State()

router = Router()

@router.callback_query(F.data == 'toggle_notifications')
async def toggle_notifications(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    status = await db.get_notifications_status(chat_id)
    await callback.answer('')
    if status:
        await callback.message.answer('Уведомления выключены')
    else:
        await callback.message.answer('Уведомления включены')

@router.callback_query(F.data == 'wb_token')
async def upd_first_step(callback: CallbackQuery, state: FSMContext):
    await state.set_state(upd_token.wb_token_state)
    await callback.answer('')
    await callback.message.answer('Введите ваш токен API Wildberries')

@router.message(upd_token.wb_token_state)
async def upd_second_step(message: Message, state: FSMContext):
    wb_token = message.text
    await db.upd_wb_token(message.chat.id, wb_token)
    await message.answer('Токен обновлён', reply_markup=to_menu)
    await state.clear()

@router.callback_query(F.data == 'upd_arts')
async def upd_articles(callback: CallbackQuery):
    await callback.answer('')
    chat_id = callback.message.chat.id
    await update_user_article(chat_id)
    await callback.message.answer('Артикулы обновлены')