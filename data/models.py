from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    telegram_id = Column(Integer, primary_key=True)
    deposit = Column(Integer)
    is_open = Column(Boolean, default=False)


class Ticket(Base):
    __tablename__ = 'tickets'

    id = Column(Integer, primary_key=True)
    position = Column(Integer, unique=True)

