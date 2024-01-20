from aiogram import Bot, Dispatcher
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from data.data import Database
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
bot = Bot(token=TOKEN)
path = os.getcwd() + "/database.sqlite"
db = Database(path)
scheduler = AsyncIOScheduler(timezone='UTC')

dp = Dispatcher(bot=bot, storage=MemoryStorage())
