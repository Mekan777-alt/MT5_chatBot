from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_session():
    keyboard = [
        [
            InlineKeyboardButton(text='Открыть тарговую сесиию', callback_data='start_session')
        ]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    return markup


def end_session():
    keyboard = [
        [
            InlineKeyboardButton(text='Закрыть текущую сессию', callback_data='end_session')
        ]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    return markup
