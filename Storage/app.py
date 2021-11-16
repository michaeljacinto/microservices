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
from sqlalchemy import and_
from stock_buy_order import StockBuyOrder
from stock_sell_order import StockSellOrder
from threading import Thread
import time
import yaml
import os

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"

with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())

# External Logging Configuration
with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info("App Conf File: %s" % app_conf_file) 
logger.info("Log Conf File: %s" % log_conf_file)

DB_ENGINE = create_engine(
    f'mysql+pymysql://{app_config["datastore"]["user"]}:{app_config["datastore"]["password"]}@{app_config["datastore"]["hostname"]}:{app_config["datastore"]["port"]}/{app_config["datastore"]["db"]}')
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

    logger.debug(
        f'Stored event SELL ORDER request with a unique id of {body["investor_id"]}')

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

    logger.debug(
        f'Stored event BUY ORDER request with a unique id of {body["investor_id"]}')

    return NoContent, 201


def get_stock_buy_orders(start_timestamp, end_timestamp):
    """ Gets new stock buy orders after the timestamp """

    session = DB_SESSION()

    start_timestamp = datetime.datetime.strptime(
        start_timestamp, "%Y-%m-%dT%H:%M:%S")
    end_timestamp = datetime.datetime.strptime(
        end_timestamp, "%Y-%m-%dT%H:%M:%S")

    readings = session.query(StockBuyOrder).filter(and_(
        StockBuyOrder.date_created >= start_timestamp, StockBuyOrder.date_created < end_timestamp))

    results_list = []

    for reading in readings:
        results_list.append(reading.to_dict())

    session.close()

    logger.info("Query for Stock Buy orders after %s and before %s returns %d results" % (
        start_timestamp, end_timestamp, len(results_list)))

    return results_list, 200


def get_stock_sell_orders(start_timestamp, end_timestamp):
    """ Gets new stock sell orders after the timestamp """

    session = DB_SESSION()

    start_timestamp = datetime.datetime.strptime(
        start_timestamp, "%Y-%m-%dT%H:%M:%S")
    end_timestamp = datetime.datetime.strptime(
        end_timestamp, "%Y-%m-%dT%H:%M:%S")

    readings = session.query(StockSellOrder).filter(and_(
        StockSellOrder.date_created >= start_timestamp, StockSellOrder.date_created < end_timestamp))

    results_list = []

    for reading in readings:
        results_list.append(reading.to_dict())

    session.close()

    logger.info("Query for Stock Sell orders after %s and before %s returns %d results" % (
        start_timestamp, end_timestamp, len(results_list)))

    return results_list, 200


def process_messages():
    """ Process event messages """
    hostname = "%s:%d" % (app_config["events"]["hostname"],
                          app_config["events"]["port"])

    retry_count = 1

    while retry_count <= app_config["max_retries"]:

        try:
            logger.info(f'Attempting to connect to reconnect to Kafka. Attempt {retry_count}..')
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(app_config["events"]["topic"])]
            logger.info("Connection to Kafka established.")
            break
            
        except Exception as e:
            logger.error(f'Connection failed. Unable to connect to Kafka..')
            time.sleep(app_config["sleep_time"])
            retry_count += 1

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
    logger.info(
        f'Connecting to DB. Hostname: {app_config["datastore"]["hostname"]}, Port: {app_config["datastore"]["port"]}')
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    app.run(port=8090)
