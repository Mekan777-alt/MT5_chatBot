import asyncio

import MetaTrader5 as mt5
from sqlalchemy import desc, or_
from sqlalchemy.exc import NoResultFound
from config import db_session, bot, session_profit, channel_id
from data.models import Ticket, Session, MessageOrders
from datetime import datetime


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
            # await asyncio.sleep(5)
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

        if positions is None:
            print("No orders on error code={}".format(mt5.last_error()))
        if not positions:
            pass
        elif len(positions) > 0:
            for position in positions:
                await create_and_check_position(position)

        all_position = await get_all_tickets_from_database()
        for pos in all_position:
            closed_orders = mt5.history_deals_get(position=pos.position)

            if len(closed_orders) >= 1:
                # Добавляем проверку времени открытия сделки перед обработкой
                open_time = datetime.fromtimestamp(closed_orders[0][2])
                current_time = datetime.now()
                time_diff = (current_time - open_time).seconds
                if time_diff >= 5:
                    await process_closed_orders(closed_orders)
    except Exception as e:
        print(f"An error occurred in position_get: {e}")


from datetime import datetime, timedelta
from data.models import Orders


async def process_closed_orders(orders):
    session_profit = 0  # Общий процент прибыли с начала сессии

    for order in orders:
        ticket = order[0]  # Уникальный идентификатор сделки (ticket)
        symbol = order[15]  # Символ (название инструмента)
        trade_type = order[4]  # Тип сделки (0 - открытие, 1 - закрытие)
        volume = order[9]  # Объем сделки
        profit = order[13]  # Прибыль
        time = order[2]  # Время сделки (timestamp)
        order_id = order[1]
        position_id = order[7]
        commision = order[11]

        ticket_to_delete = db_session.query(Ticket).filter_by(position=order[7]).first()
        print(order)
        get_order = db_session.query(Orders).filter_by(order_id=order_id).first()

        if get_order is None:
            order_to_insert = Orders(ticket_id=ticket, position_id=order[7], volume=volume,
                                     open_order=datetime.fromtimestamp(time), status=trade_type, order_id=order_id
                                     , commision=commision)
            db_session.add(order_to_insert)
            db_session.commit()
        if trade_type == 0 and get_order is None:

            orders_from_db = db_session.query(Orders).filter_by(position_id=order[7], status=1, is_closed=False).all()
            if len(orders_from_db) > 0:
                get_order = db_session.query(Orders).filter_by(order_id=order_id).first()
                get_order.is_closed = True
                db_session.commit()
                for order_from_db in orders_from_db:
                    if volume > 0 and order_from_db.is_closed == False:
                        commision_for_one_volume = commision / volume
                        new_volume = volume

                        volume -= order_from_db.volume

                        different = new_volume - volume

                        if order_from_db.volume - new_volume <= 0:
                            order_from_db.volume = 0
                        else:
                            order_from_db.volume -= new_volume
                            db_session.commit()

                        if order_from_db.volume == 0:
                            order_from_db.is_closed = True
                            db_session.commit()

                            session_id = (db_session.query(Session)
                                          .filter(Session.session_close == None)
                                          .first())
                            count = session_id.counter + 1
                            session_id.counter += 1

                            total_profit_with_commision = (profit
                                                           + commision
                                                           + commision_for_one_volume * different)

                            profit_percentage = (100 * float(total_profit_with_commision)
                                                 / float(session_id.deposit))
                            # open_trade['total_profit'] += profit_percentage

                            total_commision_for_closed_order = (commision_for_one_volume * different +
                                                                order_from_db.commision)

                            profit_percentage_without_commission = (
                                    100 * float(profit)
                                    / float(session_id.deposit))
                            session_id.profit_commision += profit_percentage

                            session_id.profit_session += profit_percentage_without_commission
                            db_session.commit()
                            trade_time = (datetime.fromtimestamp(time) - order_from_db.open_order).seconds
                            message = f"<b>📣 Сделка #{count} завершена</b>\n\n" \
                                      f"<b>Время сделки: {trade_time}сек</b>\n" \
                                      f"<b>{symbol}  {profit_percentage:.2f}%</b>\n\n" \
                                      f"<b>✅ Результат сессии: {session_id.profit_commision:.2f}% ({session_id.profit_session:.2f}%)</b>\n"

                                      # f"<b>✅ Результат сессии + ком: {session_id.profit_commision:.3f}%</b>"
                            message_order = await bot.send_message(chat_id=channel_id, text=message, parse_mode='html')
                            message_id = message_order.message_id
                            message_orders = MessageOrders(message_id=message_id, order_id=count,
                                                           profit=profit_percentage)
                            db_session.add(message_orders)
                            db_session.commit()
            orders_from_db = db_session.query(Orders).filter_by(position_id=order[7])
            flag = True
            for order in orders_from_db:
                if order.is_closed:
                    pass
                else:
                    flag = False
                    break
            if flag:
                db_session.delete(ticket_to_delete)
                db_session.commit()
            # else:
            #     for ticket_object in ticket_objects:
            #         if ticket_object.ticket_id != ticket:
            #             c_id = last_order.count_id + 1
            #             print(c_id)
            #             order_to_insert = Orders(ticket_id=ticket_object.ticket_id, position_id=order[7], volume=volume,
            #                                      open_order=datetime.fromtimestamp(time), count_id=c_id)
            #             db_session.add(order_to_insert)
            #             db_session.commit()

        elif trade_type == 1 and get_order is None:

            # orders_from_db = db_session.query(Orders).filter_by(position_id=order[7])
            #
            # sell_order = db_session.query(Orders).filter_by(ticket_id=ticket).first()
            #
            # orders_from_db_buys = db_session.query(Orders).filter_by(position_id=order[7], status=0)

            # if sell_order is None:
            #     order_to_insert = Orders(ticket_id=ticket, position_id=order[7], volume=volume,
            #                              status=1)
            #     db_session.add(order_to_insert)
            #     db_session.commit()

            # ticket_objects = db_session.query(Orders).filter_by(ticket_id=ticket)
            orders_from_db = db_session.query(Orders).filter_by(position_id=order[7], status=0, is_closed=False).all()
            # if ticket_objects.count() == 0:
            #     order_to_insert = Orders(ticket_id=ticket, position_id=order[7], volume=volume,
            #                              open_order=datetime.fromtimestamp(time), status=1)
            #     db_session.add(order_to_insert)
            #     db_session.commit()
            if len(orders_from_db) > 0:
                # sell_order_to_insert = Orders(ticket_id=ticket, position_id=order[7], volume=volume,
                #                               is_closed=True, order_id=order_id)
                # db_session.add(sell_order_to_insert)
                # db_session.commit()
                get_order = db_session.query(Orders).filter_by(order_id=order_id).first()
                get_order.is_closed = True
                db_session.commit()
                for order_from_db in orders_from_db:

                    if volume > 0 and order_from_db.is_closed == False:
                        commision_for_one_volume = commision / volume
                        new_volume = volume

                        volume -= order_from_db.volume

                        different = new_volume - volume

                        if order_from_db.volume - new_volume <= 0:
                            order_from_db.volume = 0
                        else:
                            order_from_db.volume -= new_volume
                            db_session.commit()

                        if order_from_db.volume == 0:
                            order_from_db.is_closed = True
                            db_session.commit()

                            session_id = (db_session.query(Session)
                                          .filter(Session.session_close == None)
                                          .first())
                            count = session_id.counter + 1
                            session_id.counter += 1

                            total_profit_with_commision = (profit
                                                           + commision
                                                           + commision_for_one_volume * different)

                            profit_percentage = (100 * float(total_profit_with_commision)
                                                 / float(session_id.deposit))
                            # open_trade['total_profit'] += profit_percentage

                            total_commision_for_closed_order = (commision_for_one_volume * different +
                                                                order_from_db.commision)

                            profit_percentage_without_commission = (
                                        100 * float(profit)
                                        / float(session_id.deposit))
                            session_id.profit_commision += profit_percentage

                            session_id.profit_session += profit_percentage_without_commission
                            db_session.commit()
                            trade_time = (datetime.fromtimestamp(time) - order_from_db.open_order).seconds
                            message = f"<b>📣 Сделка #{count} завершена</b>\n\n" \
                                      f"<b>Время сделки: {trade_time}сек</b>\n" \
                                      f"<b>{symbol}  {profit_percentage:.2f}%</b>\n\n" \
                                      f"<b>✅ Результат сессии: {session_id.profit_commision:.2f}% ({session_id.profit_session:.2f}%)</b>\n"
                                      # f"<b>✅ Результат сессии + ком: {session_id.profit_commision:.2f}%</b>"
                            message_order = await bot.send_message(chat_id=channel_id, text=message, parse_mode='html')
                            message_id = message_order.message_id
                            message_orders = MessageOrders(message_id=message_id, order_id=count,
                                                           profit=profit_percentage)
                            db_session.add(message_orders)
                            db_session.commit()
                orders_from_db = db_session.query(Orders).filter_by(position_id=order[7])
                flag = True
                for order in orders_from_db:
                    if order.is_closed:
                        pass
                    else:
                        flag = False
                        break
                if flag:
                    db_session.delete(ticket_to_delete)
                    db_session.commit()

        # if trade_type == 0:  # Открытие сделки
        #     if ticket not in open_trades:
        #         open_trades[ticket] = {
        #             'symbol': symbol,
        #             'buy_volume': volume,
        #             'sell_volume': 0,
        #             'total_profit': 0,
        #             'open_time': datetime.fromtimestamp(time)
        #         }
        # elif trade_type == 1:  # Закрытие сделки
        #     for open_ticket, open_trade in sorted(open_trades.items()):
        #         if open_trade['symbol'] == symbol:
        #             remaining_buy_volume = open_trade['buy_volume'] - open_trade['sell_volume']
        #             if volume <= remaining_buy_volume:
        #                 open_trade['sell_volume'] += volume
        #                 # Рассчитываем процент прибыли
        #                 profit_percentage = 100 * float(profit) / 1000
        #                 open_trade['total_profit'] += profit_percentage
        #                 session_profit += profit_percentage
        #
        #                 if open_trade['sell_volume'] == open_trade['buy_volume']:
        #                     # Сделка закрыта полностью
        #                     trade_time = (datetime.fromtimestamp(time) - open_trade['open_time']).seconds
        #                     print(f"📣 Сделка #{open_ticket} завершена\n"
        #                           f"Время сделки: {trade_time}сек\n"
        #                           f"{symbol} + {profit_percentage:.2f}%\n"
        #                           f"✅ Результат сессии: {session_profit:.2f}%|")
        #                     db_session.delete(ticket_to_delete)
        #                     db_session.commit()
        #                     del open_trades[open_ticket]
        #                 break
        #             else:
        #                 # Если проданное количество превышает купленное, разделяем сделку на две
        #                 volume_to_close = remaining_buy_volume
        #                 open_trade['sell_volume'] += volume_to_close
        #                 volume -= volume_to_close
        #                 # Рассчитываем процент прибыли для части сделки
        #                 profit_percentage_for_part = 100 * float(profit) / 1000
        #                 open_trade['total_profit'] += profit_percentage_for_part
        #                 session_profit += profit_percentage_for_part
        #
        #                 trade_time = (datetime.fromtimestamp(time) - open_trade['open_time']).seconds
        #                 print(f"📣 Сделка #{open_ticket} завершена\n"
        #                       f"Время сделки: {trade_time}сек\n"
        #                       f"{symbol} + {profit_percentage_for_part:.2f}%\n"
        #                       f"✅ Результат сессии: {session_profit:.2f}%|")
        #
        #                 # Если остался объем для закрытия, создаем новую сделку
        #                 if volume > 0:
        #                     new_ticket = max(open_trades.keys()) + 1  # Генерируем новый уникальный идентификатор сделки
        #                     open_trades[new_ticket] = {
        #                         'symbol': symbol,
        #                         'buy_volume': volume,
        #                         'sell_volume': volume,
        #                         'total_profit': 0,
        #                         'open_time': datetime.fromtimestamp(time)
        #                     }
        #                     # Рассчитываем процент прибыли для оставшейся части
        #                     profit_percentage_for_remaining = 100 * float(profit) / 1000
        #                     open_trades[new_ticket]['total_profit'] += profit_percentage_for_remaining
        #                     session_profit += profit_percentage_for_remaining
        #
        #                     print(f"📣 Сделка #{new_ticket} завершена\n"
        #                           f"Время сделки: {trade_time}сек\n"
        #                           f"{symbol} + {profit_percentage_for_remaining:.2f}%\n"
        #                           f"✅ Результат сессии: {session_profit:.2f}%|")
        #                     db_session.delete(ticket_to_delete)
        #                     db_session.commit()
        #                 break


async def get_all_tickets_from_database():
    try:
        tickets = db_session.query(Ticket).all()
        return tickets

    except Exception as e:
        print(f"Произошла ошибка при запросе всех тикетов из базы данных: {e}")
        return []

# message = f"<b>📣 Сделка #{open_ticket} завершена</b>\n\n" \
#                                       f"<b>Время сделки: {trade_time}сек</b>\n" \
#                                       f"<b>{symbol} + {profit_percentage:.2f}%</b>\n\n" \
#                                       f"<b>✅ Результат сессии: {session_profit:.2f}%</b>"
#                             await bot.send_message(chat_id=-1002037611718, text=message, parse_mode='html')
