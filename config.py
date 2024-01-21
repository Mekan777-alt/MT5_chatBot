from aiogram import Bot, Dispatcher
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from data.models import Base

load_dotenv()

TOKEN = os.getenv('TOKEN')
bot = Bot(token=TOKEN)

engine = create_engine('sqlite:///database.sqlite', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db_session = Session()

scheduler = AsyncIOScheduler(timezone='UTC')

dp = Dispatcher(bot=bot, storage=MemoryStorage())
