from aiogram.fsm.state import State, StatesGroup


class LoginSet(StatesGroup):
    login = State()
    password = State()
    server = State()


class DepositSet(StatesGroup):
    deposit = State()
