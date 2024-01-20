import asyncio
from datetime import datetime
from aiogram import types
from aiogram import Router, F
from aiogram.filters import Command
from context.login_set import LoginSet, DepositSet
from aiogram.fsm.context import FSMContext
from config import db, scheduler
from keyboard.markup import start_session, end_session
from service.mt5 import connect, position_get

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

    data = await state.get_data()
    try:
        # db.query("INSERT INTO users (ID, login, password, server, deposite, connect) VALUES (?, ?, ?, ?, ?, ?)",
        #          (int(message.from_user.id), data['login'], data['password'], data['server'], int(message.text), False))
        connecting_message = await message.answer("Выполняется подключение...")
        try:
            login = int(data['login'])
            password = str(data['password'])
            server = str(data['server'])
            if connect(account=login, password=password, server=server):
                await connecting_message.edit_text("Подключено!", reply_markup=start_session())
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


@router.callback_query(F.data == 'start_session')
async def start_session_command(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text("Введите размер депозита")

    await state.set_state(DepositSet.deposit)


@router.message(DepositSet.deposit)
async def deposit_set(message: types.Message, state: FSMContext):
    await state.update_data(deposit=message.text)
    await message.answer(f"Принято\n"
                         f"\n"
                         f"Торговая сессия открыта на сумму {message.text}$", reply_markup=end_session())
    db.query("INSERT INTO session_results (user_id, session_start_time, initial_deposit) VALUES (?, ?, ?)",
             (message.from_user.id, datetime.now(), message.text))

    scheduler.add_job(position_get, "interval", seconds=5)

    await state.clear()


@router.callback_query(F.data == 'end_session')
async def end_session_command(call: types.CallbackQuery):
    await call.message.edit_text("Текущая сессия закрыта\n"
                                 "\n"
                                 "Чтоб начать новую сессию нажмите кнопку ниже", reply_markup=start_session())

