from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Ticket(Base):
    __tablename__ = 'tickets'

    id = Column(Integer, primary_key=True)
    position = Column(Integer, unique=True)
    processed = Column(Boolean, default=False)
    total_volume = Column(Integer, default=0)
    partial_closure = Column(Boolean, default=False)


class Session(Base):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True)
    session_open = Column(DateTime)
    session_close = Column(DateTime)
    profit_session = Column(Float, default=0.0)
    profit_commision = Column(Float, default=0.0)
    counter = Column(Integer,default=0)
    deposit = Column(Integer)


class Orders(Base):
    __tablename__ = 'orders'

    ticket_id = Column(Integer, primary_key=True)

    is_closed = Column(Boolean, default=False)
    position_id = Column(Integer)
    volume = Column(Integer)
    open_order = Column(DateTime)
    status = Column(Integer)
    order_id = Column(Integer)
    commision = Column(Float, default=0.0)

class MessageOrders(Base):
    __tablename__ = 'message_orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer)
    message_id = Column(Integer)
    profit = Column(Float)
    profit_commision = Column(Float)


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    login = Column(Integer)
    password = Column(String)
    server = Column(String)




