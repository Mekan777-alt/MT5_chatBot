from datetime import datetime
import MetaTrader5 as mt5
from config import db


def initialize_mt5():
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return None
    return mt5


def login_mt5(account, server, password):
    authorized = mt5.login(account, server=server, password=password)
    if authorized:
        return True
    else:
        print("failed to connect at account #{}, error code: {}".format(account, mt5.last_error()))
        return False


def shutdown_mt5():
    mt5.shutdown()


def connect(account, server, password):
    mt5_instance = initialize_mt5()
    if mt5_instance:
        connected = login_mt5(account, server, password)
        if connected:
            return True
        else:
            shutdown_mt5()
    return False


async def create_and_check_position(positon):
    ticket = positon[0]

    date_db = positon[1]
    formatted_date_db = datetime.utcfromtimestamp(date_db).strftime('%Y-%m-%d %H:%M:%S UTC')

    update_date = positon[3]
    formatted_update_date = datetime.utcfromtimestamp(update_date).strftime('%Y-%m-%d %H:%M:%S UTC')

    volume = positon[9]

    ticket_db = db.fetchone("SELECT ticket, open_time, update_time, volume FROM deals WHERE ticket=? AND update_time=?",
                            (ticket, formatted_update_date))
    print(ticket_db)

    if ticket_db and int(ticket_db[3]) != int(volume):
        # Добавить новую запись только если объем изменился
        db.query("INSERT INTO deals (ticket, open_time, update_time, symbol, volume, profit_percentage) "
                 "VALUES (?, ?, ?, ?, ?, ?)",
                 (str(positon[0]), formatted_date_db, formatted_update_date, str(positon[16]), int(positon[9]),
                  float(positon[15])))
    elif not ticket_db:
        # Добавить новую запись, если запись с таким тикетом и временем обновления не существует
        db.query("INSERT INTO deals (ticket, open_time, update_time, symbol, volume, profit_percentage) "
                 "VALUES (?, ?, ?, ?, ?, ?)",
                 (str(positon[0]), formatted_date_db, formatted_update_date, str(positon[16]), int(positon[9]),
                  float(positon[15])))

async def position_get():
    positions = mt5.positions_get()
    if positions is None:
        print("No orders on error code={}".format(mt5.last_error()))
    elif len(positions) > 0:
        for position in positions:
            print(position)
            await create_and_check_position(position)
