import asyncio
import logging
from config import bot, dp, db, scheduler
from handler import start


async def on_shutdown(dp):
    scheduler.shutdown(wait=False)


async def main():
    logging.basicConfig(
        level=logging.INFO
    )
    dp.include_router(start.router)
    db.create_tables()
    await bot.delete_webhook(drop_pending_updates=True)
    scheduler.start()
    await asyncio.sleep(1)
    await dp.start_polling(bot)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(on_shutdown(dp))
    loop.create_task(main())
    asyncio.run(loop.run_forever())
