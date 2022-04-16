from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import ReplyKeyboardRemove

remove_keyboard = ReplyKeyboardRemove()

create_deal_keyboard = InlineKeyboardMarkup()
create_deal_keyboard.add(
    InlineKeyboardButton(
        text='Создать сделку',
        callback_data='create_deal'
    )
)
create_deal_keyboard.add(
    InlineKeyboardButton(
        text='Мои сделки',
        callback_data='my_deals'
    )
)

deals_keyboard = InlineKeyboardMarkup()
deals_keyboard.add(
    InlineKeyboardButton(
        text='5 сделок',
        callback_data='buy_deals5'
    ), InlineKeyboardButton(
        text='10 сделок',
        callback_data='buy_deals10'
    ), InlineKeyboardButton(
        text='20 сделок',
        callback_data='buy_deals20'
    ), InlineKeyboardButton(
        text='50 сделок',
        callback_data='buy_deals50'
    ), InlineKeyboardButton(
        text='1 сделка 🆕',
        callback_data='buy_deals1'
    ),
)

help_keyboard = InlineKeyboardMarkup()
help_keyboard.add(
    InlineKeyboardButton(
        text='Помощь',
        url='t.me/alexy_bl'
    )
)