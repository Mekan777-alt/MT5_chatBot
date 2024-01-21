from datetime import datetime
import MetaTrader5 as mt5
from sqlalchemy.exc import NoResultFound

from config import db_session
from data.models import Ticket, Deal, Profit


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


async def create_and_check_position(position):
    ticket = position[0]

    date_db = position[1]
    formatted_date_db = datetime.utcfromtimestamp(date_db)

    update_date = position[3]
    formatted_update_date = datetime.utcfromtimestamp(update_date)

    volume = position[9]
    try:
        ticket_object = db_session.query(Ticket).filter_by(ticket=ticket).first()

        if not ticket_object:

            ticket_object = Ticket(ticket=ticket)
            db_session.add(ticket_object)

            db_session.commit()
        ticket_id = ticket_object.id

        deal_object = db_session.query(Deal).filter_by(
            open_time=formatted_date_db,
            update_time=formatted_update_date,
            symbol=str(position[16]),
            volume=int(volume),
            ticket_id=ticket_id
        ).first()

        if deal_object is not None and (deal_object.volume is not None and int(deal_object.volume) != int(volume)):
            deal_object = Deal(
                open_time=formatted_date_db,
                update_time=formatted_update_date,
                symbol=str(position[16]),
                volume=int(deal_object.volume - volume),
                ticket_id=ticket_id
            )
            db_session.add(deal_object)

            db_session.commit()
            print("Записал в deal из-за volume")

        if not deal_object:
            deal_object = Deal(
                open_time=formatted_date_db,
                update_time=formatted_update_date,
                symbol=str(position[16]),
                volume=int(volume),
                ticket_id=ticket_id
            )
            db_session.add(deal_object)

            db_session.commit()
            print("Записал в deal")

        deal_id = deal_object.id

        profit_object = db_session.query(Profit).filter_by(
                ticket_id=ticket_id,
                deal_id=deal_id
            ).first()

        if not profit_object:
            profit_object = Profit(
                ticket_id=ticket_id,
                deal_id=deal_id,
                profit=float(position[15])
            )
            db_session.add(profit_object)
            db_session.commit()
        else:
            # Если profit_object существует, обновите его значение
            profit_object.profit = float(position[15])
            db_session.commit()
            print("Обновил значение")
    except NoResultFound:
        print("Ошибка: Не найдена запись")
        db_session.rollback()


async def position_get():
    try:
        positions = mt5.positions_get()
        if positions is None:
            # тут происходит проверка закрыта ли сделка
            print("No orders on error code={}".format(mt5.last_error()))
        elif len(positions) > 0:
            for position in positions:
                print(position)
                await create_and_check_position(position)
    except Exception as e:
        print(f"An error occurred in position_get: {e}")
