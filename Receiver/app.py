import connexion
from connexion import NoContent
import datetime
import json
from pykafka import KafkaClient 
import logging
import logging.config
import requests
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

topic = None

# def establish_kafka_connection():
""" Establish connection to Kafka """

hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"])

retry_count = 1

while retry_count <= app_config["max_retries"]:

    try:
        logger.info(f'Attempting to connect to Kafka. Attempt {retry_count}..')
        client = KafkaClient(hosts=hostname)
        topic = client.topics[str.encode(app_config["events"]["topic"])]
        producer = topic.get_sync_producer()
        logger.info("Connection to Kafka established.")
        break

    except Exception as e:
        logger.error(f'Connection failed. Unable to connect to Kafka..')
        time.sleep(app_config["sleep_time"])
        retry_count += 1


def place_stock_sell_order(body):
    """ Places stock sell order event """

    receipt_message = f'Received event SELL ORDER request with a unique id of {body["investor_id"]}'
    logger.info(receipt_message)
    
    # producer = topic.get_sync_producer()

    msg = { "type": "sell",
            "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "payload": body }
    
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))
    
    return_message = f'Returned event SELL ORDER response (id: {body["investor_id"]}) with status 201'
    logger.info(return_message)

    return NoContent, 201


def place_stock_buy_order(body):
    """ Places stock buy order event """

    receipt_message = f'Received event BUY ORDER request with a unique id of {body["investor_id"]}'
    logger.info(receipt_message)

    # producer = topic.get_sync_producer()

    msg = { "type": "buy",
            "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "payload": body }
    
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))


    return_message = f'Returned event BUY ORDER response (id: {body["investor_id"]}) with status 201'
    logger.info(return_message)

    return NoContent, 201


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", base_path="/receiver",
            strict_validation=True,
            validate_responses=True)


if __name__ == "__main__":
    app.run(port=8080)
