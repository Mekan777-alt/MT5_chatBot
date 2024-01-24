from aiogram.fsm.state import State, StatesGroup


class LoginSet(StatesGroup):
    login = State()
    password = State()
    server = State()


class DepositSet(StatesGroup):
    deposit = State()


class IDSet(StatesGroup):
    id = State()

class DeleteIDSet(StatesGroup):
    id=State()
