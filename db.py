import threading
import traceback

import mysql.connector
from mysql.connector import pooling

# 数据库连接(mysql.connection)
db_connection = []

lock = threading.Lock()

connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=10,
    host="47.120.51.172",  ### 部署到mysql所在服务器后，注意修改为localhost。
    user="user0",
    password="Taxue_#601",
    database="ordersys_db"
)

def get_db_connection():
    return connection_pool.get_connection()

# 注：do_query确保对conn、cursor的close，并且能处理异常；如果发生异常返回None
def do_query(sql,placeholders):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql,placeholders)
        return cursor.fetchall()
    except Exception as e:
        traceback.print_exc()
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()