from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_session():
    keyboard = [
        [
            InlineKeyboardButton(text='Открыть торговую сессию', callback_data='start_session')
        ]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    return markup


def end_session(id):
    keyboard = [
        [
            InlineKeyboardButton(text='Закрыть текущую сессию', callback_data=f'end_session:{id}')
        ]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    return markup
