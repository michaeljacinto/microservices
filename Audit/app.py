import connexion
from connexion import NoContent
from flask_cors import CORS, cross_origin
import logging.config
from pykafka import KafkaClient
from pykafka.common import OffsetType
import json
import yaml

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

def get_stock_sell_order(index): 
    """ Get Stock Sell Order in History """ 
    hostname = "%s:%d" % (app_config["events"]["hostname"], 
                        app_config["events"]["port"]) 
    client = KafkaClient(hosts=hostname)
    
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    # Here we reset the offset on start so that we retrieve 
    # messages at the beginning of the message queue. 
    # To prevent the for loop from blocking, we set the timeout to 
    # 100ms. There is a risk that this loop never stops if the 
    # index is large and messages are constantly being received! 
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)

    logger.info("Retrieving BP at index %d" % index) 

    count = 0

    try: 
        for msg in consumer: 
            msg_str = msg.value.decode('utf-8') 
            msg = json.loads(msg_str) 
            # Find the event at the index you want and 
            # return code 200 
            # i.e., return event, 200 

            if msg["type"] == "sell":
                if index == count:
                    return msg["payload"], 200
                count += 1

    except Exception as e:
        print(e) 
        logger.error("No more messages found") 

    logger.error("Could not find Stock Order at index %d" % index) 
    return { "message": "Not Found"}, 404 


def get_stock_buy_order(index): 
    """ Get Stock Buy Order in History """ 
    hostname = "%s:%d" % (app_config["events"]["hostname"], 
                        app_config["events"]["port"]) 

    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    # Here we reset the offset on start so that we retrieve 
    # messages at the beginning of the message queue. 
    # To prevent the for loop from blocking, we set the timeout to 
    # 100ms. There is a risk that this loop never stops if the 
    # index is large and messages are constantly being received! 
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, 
                                        consumer_timeout_ms=1000) 

    logger.info("Retrieving BP at index %d" % index) 

    count = 0

    try: 
        for msg in consumer: 
            msg_str = msg.value.decode('utf-8') 
            msg = json.loads(msg_str) 
            # Find the event at the index you want and 
            # return code 200 
            # i.e., return event, 200 

            if msg["type"] == "buy":
                if index == count:
                    return msg["payload"], 200
                count += 1

    except Exception as e:
        print(e) 
        logger.error("No more messages found") 

    logger.error("Could not find Stock Order at index %d" % index) 
    return { "message": "Not Found"}, 404 

app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app) 
app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api("openapi.yaml",
            strict_validation=True,
            validate_responses=True)

if __name__ == "__main__":
    app.run(port=8110)