import MetaTrader5 as mt5
from sqlalchemy.exc import NoResultFound
from config import db_session, session_start_time
from data.models import Ticket, User


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
    position_mt5 = position[7]

    try:
        ticket_object = db_session.query(Ticket).filter_by(position=position_mt5).first()

        if not ticket_object:

            ticket_object = Ticket(position=position_mt5)
            db_session.add(ticket_object)

            db_session.commit()
        else:
            pass
    except NoResultFound:
        print("Ошибка: Не найдена запись")
        db_session.rollback()


async def position_get():
    try:
        positions = mt5.positions_get()
        if not positions:
            pass
        elif len(positions) > 0:
            for position in positions:
                await create_and_check_position(position)

        all_position = await get_all_tickets_from_database()
        for pos in all_position:
            closed_orders = mt5.history_deals_get(position=pos.position)
            if len(closed_orders) > 1:
                await process_closed_orders(closed_orders, session_start_time)
    except Exception as e:
        print(f"An error occurred in position_get: {e}")



from datetime import datetime, timedelta

async def process_closed_orders(orders, session_start_time):
    # Создаем словарь для хранения открытых сделок по инструментам (symbol)
    open_trades = {}
    session_profit = 0  # Общий процент прибыли с начала сессии

    for order in orders:
        ticket = order[0]  # Уникальный идентификатор сделки (ticket)
        symbol = order[15]  # Символ (название инструмента)
        trade_type = order[4]  # Тип сделки (0 - открытие, 1 - закрытие)
        volume = order[9]  # Объем сделки
        profit = order[13]  # Прибыль
        time = order[2]  # Время сделки (timestamp)

        ticket_to_delete = db_session.query(Ticket).filter_by(position=order[7]).first()

        if trade_type == 0:  # Открытие сделки
            if ticket not in open_trades:
                open_trades[ticket] = {
                    'symbol': symbol,
                    'buy_volume': volume,
                    'sell_volume': 0,
                    'total_profit': 0,
                    'open_time': datetime.fromtimestamp(time)
                }
        elif trade_type == 1:  # Закрытие сделки
            for open_ticket, open_trade in sorted(open_trades.items()):
                if open_trade['symbol'] == symbol:
                    remaining_buy_volume = open_trade['buy_volume'] - open_trade['sell_volume']
                    if volume <= remaining_buy_volume:
                        open_trade['sell_volume'] += volume
                        # Рассчитываем процент прибыли
                        profit_percentage = 100 * float(profit) / 1000
                        open_trade['total_profit'] += profit_percentage
                        session_profit += profit_percentage

                        if open_trade['sell_volume'] == open_trade['buy_volume']:
                            # Сделка закрыта полностью
                            trade_time = (datetime.fromtimestamp(time) - open_trade['open_time']).seconds
                            print(f"📣 Сделка #{open_ticket} завершена\n"
                                  f"Время сделки: {trade_time}сек\n"
                                  f"{symbol} + {profit_percentage:.2f}%\n"
                                  f"✅ Результат сессии: {session_profit:.2f}%|")
                            db_session.delete(ticket_to_delete)
                            db_session.commit()
                            del open_trades[open_ticket]
                        break
                    else:
                        # Если проданное количество превышает купленное, разделяем сделку на две
                        volume_to_close = remaining_buy_volume
                        open_trade['sell_volume'] += volume_to_close
                        volume -= volume_to_close
                        # Рассчитываем процент прибыли для части сделки
                        profit_percentage_for_part = 100 * float(profit) / 1000
                        open_trade['total_profit'] += profit_percentage_for_part
                        session_profit += profit_percentage_for_part

                        trade_time = (datetime.fromtimestamp(time) - open_trade['open_time']).seconds
                        print(f"📣 Сделка #{open_ticket} завершена\n"
                              f"Время сделки: {trade_time}сек\n"
                              f"{symbol} + {profit_percentage_for_part:.2f}%\n"
                              f"✅ Результат сессии: {session_profit:.2f}%|")

                        # Если остался объем для закрытия, создаем новую сделку
                        if volume > 0:
                            new_ticket = max(open_trades.keys()) + 1  # Генерируем новый уникальный идентификатор сделки
                            open_trades[new_ticket] = {
                                'symbol': symbol,
                                'buy_volume': volume,
                                'sell_volume': volume,
                                'total_profit': 0,
                                'open_time': datetime.fromtimestamp(time)
                            }
                            # Рассчитываем процент прибыли для оставшейся части
                            profit_percentage_for_remaining = 100 * float(profit) / 1000
                            open_trades[new_ticket]['total_profit'] += profit_percentage_for_remaining
                            session_profit += profit_percentage_for_remaining

                            print(f"📣 Сделка #{new_ticket} завершена\n"
                                  f"Время сделки: {trade_time}сек\n"
                                  f"{symbol} + {profit_percentage_for_remaining:.2f}%\n"
                                  f"✅ Результат сессии: {session_profit:.2f}%|")
                            db_session.delete(ticket_to_delete)
                            db_session.commit()
                        break


async def get_all_tickets_from_database():
    try:
        tickets = db_session.query(Ticket).all()
        return tickets

    except Exception as e:
        print(f"Произошла ошибка при запросе всех тикетов из базы данных: {e}")
        return []



# ПРОХОДИТ ПО 3 ТЕСТАМ
# async def process_closed_orders(orders):
#     # Создаем словарь для хранения открытых сделок по инструментам (symbol)
#     open_trades = {}
#
#     for order in orders:
#         ticket = order[0]  # Уникальный идентификатор сделки (ticket)
#         symbol = order[15]  # Символ (название инструмента)
#         trade_type = order[4] # Тип сделки (0 - открытие, 1 - закрытие)
#         volume = order[9]  # Объем сделки
#         profit = order[13]  # Прибыль
#         time = order[2]  # Время сделки (timestamp)
#
#         if trade_type == 0:  # Открытие сделки
#             if ticket not in open_trades:
#                 open_trades[ticket] = {
#                     'symbol': symbol,
#                     'buy_volume': volume,
#                     'sell_volume': 0,
#                     'total_profit': 0,
#                     'open_time': time
#                 }
#         elif trade_type == 1:  # Закрытие сделки
#             for open_ticket, open_trade in sorted(open_trades.items()):
#                 if open_trade['symbol'] == symbol:
#                     remaining_buy_volume = open_trade['buy_volume'] - open_trade['sell_volume']
#                     if volume <= remaining_buy_volume:
#                         open_trade['sell_volume'] += volume
#                         # Рассчитываем процент прибыли
#                         initial_deposit = 1000  # Ваш начальный депозит
#                         profit_percentage = 100 * float(profit) / initial_deposit
#                         open_trade['total_profit'] += profit_percentage
#
#                         if open_trade['sell_volume'] == open_trade['buy_volume']:
#                             # Сделка закрыта полностью, добавьте здесь логику сохранения результатов в базу данных
#                             print(f"Сделка закрыта для {open_ticket}. "
#                                   f"Куплено: {open_trade['buy_volume']} шт. "
#                                   f"Продано: {open_trade['sell_volume']} шт. "
#                                   f"Общий процент прибыли: {open_trade['total_profit']:.3f}% ")
#                             del open_trades[open_ticket]
#                             break  # Прерываем цикл, так как закрыли одну из сделок
#                         else:
#                             pass
#                         break
#                     else:
#                         print(f"Внимание! Продажа контрактов ({volume} шт.) превышает доступное количество ({remaining_buy_volume} шт.) "
#                               f"для сделки с {symbol}. Продажа будет произведена только для доступного объема.")
#                         # Создаем новую сделку, так как разница во времени больше 5 секунд
#                         open_trades[ticket] = {
#                             'symbol': symbol,
#                             'buy_volume': volume,
#                             'sell_volume': 0,
#                             'total_profit': 0,
#                             'open_time': time
#                         }
#                         break
#                         # Можно добавить дополнительную логику, если нужно обработать частичное закрытие сделки