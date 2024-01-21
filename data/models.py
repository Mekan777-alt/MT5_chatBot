from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Ticket(Base):
    __tablename__ = 'tickets'

    id = Column(Integer, primary_key=True)
    ticket = Column(Integer, unique=True)
    deals = relationship('Deal', order_by='Deal.id', back_populates='ticket')


class Deal(Base):
    __tablename__ = 'deals'

    id = Column(Integer, primary_key=True)
    open_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow)
    symbol = Column(String)
    volume = Column(Integer)
    ticket_id = Column(Integer, ForeignKey('tickets.id'))
    ticket = relationship('Ticket', back_populates='deals')
    profit = relationship('Profit', back_populates='deal')


class Profit(Base):
    __tablename__ = 'profit'

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey('tickets.id'))
    deal_id = Column(Integer, ForeignKey('deals.id'))
    profit = Column(Float, nullable=False)
    deal = relationship('Deal', back_populates='profit')
