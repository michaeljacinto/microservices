from sqlalchemy import Column, Integer, String, DateTime, Float
from base import Base
import datetime


class StockSellOrder(Base):
    """ Stock Sell Order """

    __tablename__ = "stock_sell_orders"

    id = Column(Integer, primary_key=True)
    investor_id = Column(String(250), nullable=False)
    stock_id = Column(String(250), nullable=False)
    ask_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    timestamp = Column(String(100), nullable=False)
    date_created = Column(DateTime, nullable=False)


    def __init__(self, investor_id, stock_id, ask_price, quantity, timestamp):
        """ Initializes a stock sell order """

        self.investor_id = investor_id
        self.stock_id = stock_id
        self.ask_price = ask_price
        self.quantity = quantity
        self.timestamp = timestamp
        self.date_created = datetime.datetime.now() # Sets the date/time record is created


    def to_dict(self):
        """ Dictionary Representation of a stock sell order """
        
        dict = {}
        dict['id'] = self.id
        dict['investor_id'] = self.investor_id
        dict['stock_id'] = self.stock_id
        dict['ask_price'] = self.ask_price
        dict['quantity']= self.quantity
        dict['timestamp'] = self.timestamp
        dict['date_created'] = self.date_created
        return dict
