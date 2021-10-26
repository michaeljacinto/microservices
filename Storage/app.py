from base import Base
import connexion
from connexion import NoContent
import datetime
import json
from pykafka import KafkaClient
import logging
import logging.config
from pykafka.common import OffsetType
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from stock_buy_order import StockBuyOrder
from stock_sell_order import StockSellOrder
from threading import Thread 
import yaml

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

DB_ENGINE = create_engine(f'mysql+pymysql://{app_config["datastore"]["user"]}:{app_config["datastore"]["password"]}@{app_config["datastore"]["hostname"]}:{app_config["datastore"]["port"]}/{app_config["datastore"]["db"]}')
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


def place_stock_sell_order(body):
    """ Receives a stock sell order """

    session = DB_SESSION()

    sso = StockSellOrder(body['investor_id'],
                       body['stock_id'],
                       body['ask_price'],
                       body['quantity'],
                       body['timestamp'])
    
    session.add(sso)

    session.commit()
    session.close()

    logger.debug(f'Stored event SELL ORDER request with a unique id of {body["investor_id"]}')

    return NoContent, 201


def place_stock_buy_order(body):
    """ Recieves a stock buy order """

    session = DB_SESSION()
    sbo = StockBuyOrder(body['investor_id'],
                       body['stock_id'],
                       body['bid_price'],
                       body['quantity'],
                       body['timestamp'])

    session.add(sbo)

    session.commit()
    session.close()

    logger.debug(f'Stored event BUY ORDER request with a unique id of {body["investor_id"]}')

    return NoContent, 201


def get_stock_buy_orders(timestamp):
    """ Gets new stock buy orders after the timestamp """

    session = DB_SESSION()

    timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S") # being parsed


    readings = session.query(StockBuyOrder).filter(StockBuyOrder.date_created >= timestamp_datetime)

    results_list = [] 
    
    for reading in readings: results_list.append(reading.to_dict())

    session.close() 

    logger.info("Query for Stock Buy orders after %s returns %d results" % (timestamp, len(results_list))) 
    
    return results_list, 200


def get_stock_sell_orders(timestamp):
    """ Gets new stock sell orders after the timestamp """

    session = DB_SESSION()
    timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S") 
    readings = session.query(StockSellOrder).filter(StockSellOrder.date_created >= timestamp_datetime)

    results_list = [] 
    
    for reading in readings: results_list.append(reading.to_dict())

    session.close() 

    logger.info("Query for Stock Sell orders after %s returns %d results" % (timestamp, len(results_list))) 
    
    return results_list, 200


def process_messages():
    """ Process event messages """ 
    hostname = "%s:%d" % (app_config["events"]["hostname"], 
                        app_config["events"]["port"]) 

    client = KafkaClient(hosts=hostname) 
    topic = client.topics[str.encode(app_config["events"]["topic"])] 
    
    # Create a consume on a consumer group, that only reads new messages 
    # (uncommitted messages) when the service re-starts (i.e., it doesn't 
    # read all the old messages from the history in the message queue). 
    consumer = topic.get_simple_consumer(consumer_group=b'event_group', 
                                        reset_offset_on_start=False, 
                                        auto_offset_reset=OffsetType.LATEST)
    
    # This is blocking - it will wait for a new message 
    for msg in consumer: 

        msg_str = msg.value.decode('utf-8') 
        msg = json.loads(msg_str) 
        logger.info("Message: %s" % msg) 
        
        payload = msg["payload"] 
        
        if msg["type"] == "sell":
            place_stock_sell_order(payload)

        elif msg["type"] == "buy":
            place_stock_buy_order(payload)

        # Commit the new message as being read 
        consumer.commit_offsets() 


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml",
            strict_validation=True,
            validate_responses=True)


if __name__ == "__main__":
    logger.info(f'Connecting to DB. Hostname: {app_config["datastore"]["hostname"]}, Port: {app_config["datastore"]["port"]}')
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    app.run(port=8090)