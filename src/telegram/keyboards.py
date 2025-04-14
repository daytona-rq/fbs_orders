from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.web_app_info import WebAppInfo

back_button = [InlineKeyboardButton(text='<< Меню', callback_data='back')]

to_menu = InlineKeyboardMarkup(inline_keyboard=[back_button])

start_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Пробный период', callback_data='trial'),
    InlineKeyboardButton(text='Настройки пользователя', callback_data='user_settings')], 
    [InlineKeyboardButton(text='Гайд', callback_data='guide'),
    InlineKeyboardButton(text='Статус подписки', callback_data='subscribe')]])

trial_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Активировать пробный период', callback_data='activate_trial')],
    back_button
])

help_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Видео', url='example.com'), 
    InlineKeyboardButton(text='Текстовый гайд', callback_data='text_guide')],
    back_button])

sub_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Подписка', callback_data='get_sub')],
    back_button
])

user_settings = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Токен WB', callback_data='wb_token'), 
     InlineKeyboardButton(text='Обновить артикулы', web_app=WebAppInfo(url='https://rnqfv-89-250-167-62.a.free.pinggy.link'))],
    [InlineKeyboardButton(text='Вкл/Выкл уведомления', callback_data='toggle_notifications')],
    
    back_button
])

