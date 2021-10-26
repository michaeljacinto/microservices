import mysql.connector
import yaml

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

db_conn = mysql.connector.connect(host=f'{app_config["datastore"]["hostname"]}', 
                                    user=f'{app_config["datastore"]["user"]}', 
                                    password=f'{app_config["datastore"]["password"]}', 
                                    database=f'{app_config["datastore"]["db"]}')

# conn = sqlite3.connect('readings.sqlite')

db_cursor = db_conn.cursor()
db_cursor.execute('''
          CREATE TABLE IF NOT EXISTS stock_sell_orders
          (id INT NOT NULL AUTO_INCREMENT, 
           investor_id VARCHAR(250) NOT NULL,
           stock_id TEXT NOT NULL,
           ask_price REAL NOT NULL,
           quantity INT NOT NULL,
           timestamp VARCHAR(100) NOT NULL,
           date_created VARCHAR(100) NOT NULL,
           CONSTRAINT stock_sell_order_pk PRIMARY KEY (id))
          ''')

db_cursor.execute('''
          CREATE TABLE IF NOT EXISTS stock_buy_orders
          (id INT NOT NULL AUTO_INCREMENT, 
           investor_id VARCHAR(250) NOT NULL,
           stock_id TEXT NOT NULL,
           bid_price REAL NOT NULL,
           quantity INT NOT NULL,
           timestamp VARCHAR(100) NOT NULL,
           date_created VARCHAR(100) NOT NULL,
           CONSTRAINT stock_buy_order_pk PRIMARY KEY (id))
          ''')

db_conn.commit()
db_conn.close()
