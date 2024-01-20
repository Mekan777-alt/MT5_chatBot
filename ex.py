import asyncio
import logging
from datetime import datetime
import MetaTrader5 as mt5
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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
        connected = login_mt5(account=account, server=server, password=password)
        if connected:
            return True
        else:
            shutdown_mt5()
    return None


class OpenDeal:
    def __init__(self, ticket, open_time, symbol, volume):
        self.ticket = ticket
        self.open_time = open_time
        self.symbol = symbol
        self.volume = volume
        # self.profit_percentage = profit_percentage

    def __str__(self):
        return f"Ticket: {self.ticket} - {self.open_time} - {self.symbol} - {self.volume}"


open_deals = []
session_start_time = datetime.now()

async def create_and_check_position(position):
    ticket_position = position.ticket

    date_position = position[1]
    formatted_date_position = datetime.utcfromtimestamp(date_position).strftime('%Y-%m-%d %H:%M:%S UTC')

    update_date_position = position[3]
    formatted_update_date = datetime.utcfromtimestamp(update_date_position).strftime('%Y-%m-%d %H:%M:%S UTC')

    volume = position[9]
    # profit_percentage = position.profit

    # Проверяем, открыта ли сделка с таким тикетом
    open_deal = next((deal for deal in open_deals if deal.volume == volume), None)
    print(open_deal)

    if not open_deal and int(volume) > 0:
        # Открываем новую сделку
        new_open_deal = OpenDeal(
            ticket=str(position.ticket),
            open_time=formatted_date_position,
            symbol=str(position[16]),
            volume=int(position[9]),
            # profit_percentage=float(position.pro)
        )
        open_deals.append(new_open_deal)
        for deal in open_deals:
            print(deal)
        print(f"Added new deal with ticket {ticket_position} at {formatted_date_position}")
        print(f"Opened deal with ticket {ticket_position}")
    elif open_deal and int(volume) == 0:
        # Закрываем существующую сделку
        open_deal.volume -= 1  # Уменьшаем объем сделки на 1 (продали 1 штуку)
        print(f"Closed deal with ticket {ticket_position}")
    elif open_deal and int(volume) > open_deal.volume or int(volume) < open_deal.volume:
        # Обновление существующей сделки
        open_deal.volume = int(volume)
        # open_deal.profit_percentage = float(profit_percentage)
        print(f"Updated deal with ticket {ticket_position} at {formatted_update_date}")

    # Закрытие сделки
    closed_deals = [deal for deal in open_deals if deal.volume == 0]
    for deal in closed_deals:
        # Сделка закрыта, выводим результат, удаляем её из списка открытых сделок
        open_deals.remove(deal)
        print(f"Closed deal with ticket {deal.ticket}")


    # Обработка результатов сессии
    # session_duration = (datetime.now() - session_start_time).total_seconds()
    # total_profit = sum(deal.profit_percentage for deal in open_deals)
    # session_result = total_profit / session_duration * 100  # Приведение к процентам
    # print(f"Session result: {session_result:.2f}%")

# Дополнительная логика, если необходимо продолжать отслеживать сделки в течение сессии
# Используйте асинхронный планировщик для вызова position_get каждые 5 секунд


async def position_get():
    orders = mt5.positions_get()
    if orders is None:
        print("No orders on error code={}".format(mt5.last_error()))
    elif len(orders) > 0:
        for order in orders:
            print(order)
            await create_and_check_position(order)


async def main():
    mt5_instance = connect(account=3154590, server='Just2Trade-MT5', password='6jOiD@Ok')

    if mt5_instance:
        scheduler = AsyncIOScheduler(timezone='UTC')
        scheduler.add_job(position_get, "interval", seconds=5)
        print("Initial open deals:", open_deals)
        print("Initial session start time:", session_start_time)
        scheduler.start()
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            scheduler.shutdown(wait=False)
    else:
        print("Connection failed. Shutting down.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
