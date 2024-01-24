from datetime import datetime

from aiogram import Bot, Dispatcher
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from data.models import Base

load_dotenv()

TOKEN = '6641348620:AAHtVi-9ocoX74f_9DkNQP6kYbKZVz0Mi3c'
bot = Bot(token=TOKEN)

engine = create_engine('sqlite:///database.sqlite', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db_session = Session()
session_profit = 0
# Словарь для отслеживания уже обработанных сделок
processed_deals = {}

channel_id = -1002037611718
scheduler = AsyncIOScheduler(timezone='UTC')

dp = Dispatcher(bot=bot, storage=MemoryStorage())
