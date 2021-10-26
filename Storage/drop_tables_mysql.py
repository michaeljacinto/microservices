import mysql.connector
import yaml

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())
    
db_conn = mysql.connector.connect(host=f'{app_config["datastore"]["hostname"]}', 
                                    user=f'{app_config["datastore"]["user"]}', 
                                    password=f'{app_config["datastore"]["password"]}', 
                                    database=f'{app_config["datastore"]["db"]}')

db_cursor = db_conn.cursor()

db_cursor.execute('''
                DROP TABLE IF EXISTS stock_buy_orders
                ''')

db_cursor.execute('''
                DROP TABLE IF EXISTS stock_sell_orders
                ''')

db_conn.commit()
db_conn.close()
