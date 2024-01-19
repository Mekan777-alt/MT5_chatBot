import asyncio
import logging
from config import bot, dp, db
from handler import start


async def main():
    logging.basicConfig(
        level=logging.INFO
    )
    db.create_tables()
    dp.include_router(start.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
