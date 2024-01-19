from aiogram import types
from aiogram import Router
from aiogram.filters import Command
from context.login_set import LoginSet
from aiogram.fsm.context import FSMContext
from config import db
from service.mt5 import connect

router = Router()


@router.message(Command('start'))
async def start(message: types.Message, state: FSMContext):
    await message.answer("Здравствуйте!\n"
                         "\n"
                         "Введите логин")

    await state.set_state(LoginSet.login)


@router.message(LoginSet.login)
async def login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text)

    await message.answer("Введите пароль:")
    await state.set_state(LoginSet.password)


@router.message(LoginSet.password)
async def password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)

    await message.answer("Введите сервер:")
    await state.set_state(LoginSet.server)


@router.message(LoginSet.server)
async def broker(message: types.Message, state: FSMContext):
    await state.update_data(server=message.text)

    await message.answer("Введите депозит")
    await state.set_state(LoginSet.deposite)


@router.message(LoginSet.deposite)
async def deposite(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        # db.query("INSERT INTO users (ID, login, password, server, deposite, connect) VALUES (?, ?, ?, ?, ?, ?)",
        #          (int(message.from_user.id), data['login'], data['password'], data['server'], int(message.text), False))
        await message.answer("Выполняется подключение...")
        try:
            login = int(data['login'])
            password = str(data['password'])
            server = str(data['server'])
            if connect(account=login, password=password, server=server):
                await message.answer("Подключено!")
                await state.clear()
            else:
                await message.answer("Нет подключения!\n"
                                     "\n"
                                     "Повторите попытку /start")
                await state.clear()
        except ValueError as val:
            await message.answer(f"Ошибка: {val}\n"
                                 f"\n"
                                 f"Перезапустите бота /start")
            await state.clear()
    except ValueError as val:
        await message.answer(f"Ошибка: {val}\n"
                             f"\n"
                             f"Перезапустите бота /start")
        await state.clear()

