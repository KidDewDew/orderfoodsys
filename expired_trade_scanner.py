import threading
import time
import traceback
from datetime import datetime, timedelta

from numpy.core.defchararray import translate

import db

# 过期待支付订单扫描类
# 由于用户可能一直没有支付订单，并且前端没有成功地告诉后端订单取消，则需要定时扫描来删除超时订单，
# 对于超时订单，需要把它占据的库存返还给shop.
class TradeOrderScanner:
    def __init__(self):
        self.scan_interval = 60 #一分钟扫描一次
        self.timeout = 300 # 5分钟没有支付完成的订单，认为用户已经放弃该订单
        self.is_running = False

    def start(self):
        self.is_running = True
        thread = threading.Thread(target=self._loop, daemon=True)
        thread.start()
        print(f"TradeOrderScanner started.")

    def _loop(self):
        while self.is_running:
            self._scan()
            time.sleep(self.scan_interval)

    # 完成一次扫描
    def _scan(self):
        # 过期时间
        expired_datetime = datetime.now() - timedelta(seconds=self.timeout)
        try:
            conn = db.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT out_trade_no FROM alipay_trade "
                           "WHERE create_time < %s ORDER BY create_time LIMIT 100 FOR UPDATE",
                           (expired_datetime,))

        except Exception as e:
            traceback.print_exc()
        finally:
            if(cursor): cursor.close()
            if(conn): conn.close()

