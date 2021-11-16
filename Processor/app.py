import connexion
from connexion import NoContent
# import datetime
from datetime import datetime
from datetime import timedelta
from flask_cors import CORS, cross_origin
import os
import json
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import logging.config
import requests
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

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# External Logging Configuration
with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info("App Conf File: %s" % app_conf_file) 
logger.info("Log Conf File: %s" % log_conf_file)

logger = logging.getLogger('basicLogger')
json_file = app_config['datastore']['filename']


def get_stats():
    """ Retrieve stock order stats """

    if os.path.exists(json_file):
        logger.info("Request to get all stock order stats has started.")

        with open(json_file, 'r') as file_handle:
            current_stats = json.loads(file_handle.read())

        logger.info("Request to get all stock order stats has completed.")
        return current_stats, 200

    else:
        logger.error("Statistics do not exist")
        return NoContent, 404


def populate_stats():
    """ Periodically update stats """

    logger.info("Starting periodic process..")
    current_stats = get_stats()

    if not os.path.isfile(json_file):

        default_stats = {
            "num_stock_sell_orders": 0,
            "max_stock_sell_qty": 0,
            "min_stock_ask_price": 10000.00,
            "num_stock_buy_orders": 0,
            "max_stock_buy_qty": 0,
            "min_stock_bid_price": 10000.00,
            "last_updated": "2016-08-29T09:12:33"
        }

        with open(json_file, 'w') as file_handle:
            file_handle.write(json.dumps(default_stats, indent=4))
            return

    if current_stats[1] == 404:
        logger.error(
            "There was an issue populating stats. Please check the log files.")
        return

    current_stats = current_stats[0]

    current_datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    buy_orders = requests.get(app_config["buy"]["url"],
                              params={
        "start_timestamp": current_stats['last_updated'],
        "end_timestamp": current_datetime
    }).json()

    sell_orders = requests.get(app_config["sell"]["url"],
                               params={
        "start_timestamp": current_stats['last_updated'],
        "end_timestamp": current_datetime
    }).json()

    count_sell_orders = len(sell_orders)
    count_buy_orders = len(buy_orders)

    updated_stats = {
        "num_stock_sell_orders": current_stats['num_stock_sell_orders'] + count_sell_orders,
        "max_stock_sell_qty": get_max_value(sell_orders, current_stats, 'quantity', 'max_stock_sell_qty'),
        "min_stock_ask_price": get_min_value(sell_orders, current_stats, 'ask_price', 'min_stock_ask_price'),
        "num_stock_buy_orders": current_stats['num_stock_buy_orders'] + count_buy_orders,
        "max_stock_buy_qty": get_max_value(buy_orders, current_stats, 'quantity', 'max_stock_buy_qty'),
        "min_stock_bid_price": get_min_value(buy_orders, current_stats, 'bid_price', 'min_stock_bid_price'),
        "last_updated": current_datetime
    }

    # Write updated stats to json file
    # Log events recieved and updated stats
    with open(json_file, 'w') as file_handle:
        total_events = count_buy_orders + count_sell_orders
        file_handle.write(json.dumps(updated_stats, indent=4))
        logger.info(
            f'Total Events received from GET request: {total_events}')
        logger.debug(updated_stats)


def get_max_value(order_list, stats, order_list_key, stats_key):
    """ Get max value between orders and current stats """

    current_max_value = stats[stats_key]

    if len(order_list) == 0:
        return current_max_value
    max_list_value = max(order_list, key=lambda x: x[order_list_key])[
        order_list_key]

    return max_list_value if max_list_value > current_max_value else current_max_value


def get_min_value(order_list, stats, order_list_key, stats_key):
    """ Get min value between orders and current stats """

    current_min_value = stats[stats_key]

    if len(order_list) == 0:
        return current_min_value

    min_list_value = min(order_list, key=lambda x: x[order_list_key])[
        order_list_key]

    return min_list_value if min_list_value < current_min_value else current_min_value


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats,
                  'interval',
                  seconds=app_config['scheduler']['period_sec'])
    sched.start()


app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app) 
app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api("openapi.yaml",
            strict_validation=True,
            validate_responses=True)


if __name__ == "__main__":
    # Run our standalone gevent server
    init_scheduler()
    app.run(port=8100, use_reloader=False)
