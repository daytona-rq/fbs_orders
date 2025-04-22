from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.web_app_info import WebAppInfo


app_link = 'https://ir-wb-auto.ru/'

back_button = [InlineKeyboardButton(text='<< Меню', callback_data='back')]

to_menu = InlineKeyboardMarkup(inline_keyboard=[back_button])

def create_payment_kb(payment_url: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Оплатить', url=payment_url)], 
            back_button
        ]
    )

start_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Пробный период', callback_data='trial'),
    InlineKeyboardButton(text='Настройки пользователя', callback_data='user_settings')], 
    [InlineKeyboardButton(text='Гайд', callback_data='guide'),
    InlineKeyboardButton(text='Статус подписки', callback_data='subscribe_status')]])

trial_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Активировать пробный период', callback_data='activate_trial')],
    back_button
])

help_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Видео', url='example.com'), 
    InlineKeyboardButton(text='Текстовый гайд', callback_data='text_guide')],
    back_button])

sub_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Оформить подписку', callback_data='buy_sub')],
    back_button
])

user_settings = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Токен WB', callback_data='wb_token'), 
     InlineKeyboardButton(text='Обновить артикулы', web_app=WebAppInfo(url=app_link))],
    [InlineKeyboardButton(text='Вкл/Выкл уведомления', callback_data='toggle_notifications')],
    
    back_button
])

