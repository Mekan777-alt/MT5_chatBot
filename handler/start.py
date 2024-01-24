import datetime
from aiogram.types import callback_query
from data.models import Session, MessageOrders, User
from aiogram import types
from aiogram import Router, F
from aiogram.filters import Command
from context.login_set import LoginSet, DepositSet, IDSet, DeleteIDSet
from aiogram.fsm.context import FSMContext
from config import scheduler, db_session, bot, channel_id, dp
from keyboard.markup import start_session, end_session
from service.mt5 import connect, position_get, shutdown_mt5

router = Router()


@router.message(Command('new'))
async def new(message: types.Message, state: FSMContext):
    await message.answer("Здравствуйте!\n"
                         "\n"
                         "Введите логин")

    await state.set_state(LoginSet.login)


@router.message(Command('delete'))
async def delete(message: types.Message):
    print(message.text)
    text = message.text.split()
    message_order = db_session.query(MessageOrders).filter(MessageOrders.order_id == int(text[1])).first()
    session_id = db_session.query(Session).filter(Session.session_close == None).first()
    session_id.profit_session += message_order.profit
    print(text[1])
    print(message_order.message_id)
    await bot.delete_message(chat_id=channel_id, message_id=int(message_order.message_id))


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

        connecting_message = await message.answer("Выполняется подключение...")
        try:
            login = int(data['login'])
            password = str(data['password'])
            server = str(data['server'])
            user = User(login=login, password=password, server=server)
            db_session.add(user)
            db_session.commit()
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

    session = Session(session_open=datetime.datetime.now(), deposit=int(message.text))

    db_session.add(session)
    db_session.commit()

    session_id = db_session.query(Session).filter(Session.id == session.id).first()
    await message.answer(f"Принято\n"
                         f"\n"
                         f"Торговая сессия открыта на сумму {message.text}$", reply_markup=end_session(session.id))
    print(session_id.id)
    scheduler.add_job(position_get, "interval", seconds=2, id=str(session_id.id))

    await state.clear()


@router.callback_query(F.data.startswith('end_session'))
async def end_session_command(call: types.CallbackQuery):
    _, session_id = call.data.split(':')

    session = db_session.query(Session).filter(Session.id == session_id).first()
    session.session_close = datetime.datetime.now()
    db_session.commit()
    db_session.query(MessageOrders).delete()
    db_session.commit()
    scheduler.remove_job(session_id)
    shutdown_mt5()
    await call.message.edit_text("Текущая сессия закрыта\n"
                                 "Для подключения нажмите команду /connect")


@router.message(Command("delete_account"))
async def delete_account_command(message: types.Message, state: FSMContext):
    users_list = db_session.query(User).all()
    result = ""
    for user in users_list:
        result += f"ID={user.id}. Login={user.login} Password={user.password} Server={user.server}\n"

    await message.answer(result)
    await message.answer("Введите ID аккаунта к которому хотите подключиться")
    await state.set_state(DeleteIDSet.id)


@router.message(DeleteIDSet.id)
async def deleting(message: types.Message, state: FSMContext):
    id = message.text
    user = db_session.query(User).filter_by(id=id).first()
    if user:
        db_session.delete(user)
        db_session.commit()
        await message.answer("Удалено")
        await state.clear()
    else:
        await message.answer("Аккаунта с таким ID не существует")
    await message.answer("Выберите команду")


@router.message(Command("list"))
async def list_commands(message: types.Message):
    users_list = db_session.query(User).all()
    result = ""
    if len(users_list) > 0:
        for user in users_list:
            result += f"ID={user.id}. Login={user.login} Password={user.password} Server={user.server}\n"
        await message.answer(result)
    else:
        await message.answer("У вас нет аккаунтов")
    print(users_list)


@router.message(Command('start'))
async def start(message: types.Message):
    await set_default_commands(bot)
    await message.answer("Выберите команду")


@router.message(Command('connect'))
async def connect_command(message: types.Message, state: FSMContext):
    users_list = db_session.query(User).all()
    result = ""
    if len(users_list) > 0:
        for user in users_list:
            result += f"ID={user.id}. Login={user.login} Password={user.password} Server={user.server}\n"

        await message.answer(result)
        await message.answer("Введите ID аккаунта к которому хотите подключиться")
        await state.set_state(IDSet.id)
    else:
        await message.answer("У вас нет аккаунтов создайте новый /new")

@router.message(IDSet.id)
async def connecting(message: types.Message, state: FSMContext):
    id = message.text
    user = db_session.query(User).filter_by(id=id).first()
    if user:
        try:
            if connect(account=user.login, password=user.password, server=user.server):

                await message.answer("Подключено", reply_markup=start_session())
                await state.clear()
            else:
                await message.answer("Не подключено! Повторите снова")
        except Exception as ex:
            print(f"Ошибка!!  - {ex}")
    else:
        await message.answer("Аккаунта с таким ID не существует")


async def set_default_commands(bot):
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Запустить/Перезапустить бота"),
        types.BotCommand(command="new", description="Добавить аккаунт"),
        types.BotCommand(command="delete_account", description="Удалить аккаунт"),
        types.BotCommand(command="list", description="Список аккаунтов"),
        types.BotCommand(command="connect", description="Подключиться к аккаунту")
    ])
