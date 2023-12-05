"""
为了可以实盘、模拟盘切换
对class TradeBase:部分代码进行注释
代码位置：_base.py，33行至39行
"""

from crawler.myokx import app
import settings
import threading
from crawler.utils.db import Connect
import json
import redis
import time
from functools import wraps
from loguru import logger

# proxies = {
#     'http': 'socks5h://15755149931sct-5:8ivtkleb@183.56.143.53:10607',
#     'https': 'socks5h://15755149931sct-5:8ivtkleb@183.56.143.53:10607'
#     # 'all': 'socks5h://15755149931sct-5:8ivtkleb@38.147.173.111:5003'
# }

logger.remove()  # 移除所有默认的handler


def thread_log_filter(record, user_id, task_id):
    """过滤器，只接收包含特定线程标记的日志记录"""
    return record["extra"].get("user_id") == user_id and record["extra"].get("task_id") == task_id


def retry(max_attempts=5, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:  # 捕获所有异常
                    print(f"操作失败，原因: {e}. 正在重试...")
                    attempts += 1
                    time.sleep(delay)
            print("多次尝试失败，放弃本次交易操作。")

        return wrapper

    return decorator


class RetryDecoratorProxy:
    def __init__(self, obj):
        self._obj = obj

    def __getattr__(self, name):
        attr = getattr(self._obj, name)
        if callable(attr):
            return retry()(attr)
        return attr


class RetryNetworkOperations:
    def __init__(self, network_operations):
        self._operations = network_operations

    def __getattr__(self, name):
        attr = getattr(self._operations, name)
        # 如果 attr 是对象实例，为其方法应用 retry 装饰器
        if not callable(attr) and not name.startswith("__"):
            return RetryDecoratorProxy(attr)
        return attr


class Trader(threading.Thread):
    def __init__(self, task_id, order_type, trader_platform, uniqueName, follow_type, sums, lever_set, first_order_set,
                 api_id,
                 user_id, instId, mgnMode, posSide, lever, openTime=None, openAvgPx=None, availSubPos=None,
                 old_availSubPos=None, new_availSubPos=None):
        super(Trader, self).__init__()
        self.task_id = task_id
        self.order_type = order_type
        self.trader_platform = trader_platform
        self.uniqueName = uniqueName
        self.follow_type = follow_type
        self.sums = sums
        self.lever_set = lever_set
        self.first_order_set = first_order_set
        self.api_id = api_id
        self.user_id = user_id
        self.availSubPos = availSubPos
        self.old_availSubPos = old_availSubPos
        self.new_availSubPos = new_availSubPos
        self.instId = instId
        self.mgnMode = mgnMode
        self.posSide = posSide
        self.lever = int(lever)
        self.openTime = openTime
        self.openAvgPx = openAvgPx
        self.logger_id = None
        self.thread_logger = None
        self.obj = None
        self.flag = None

    def setup_logger(self):
        log_file = f"trade_logs/{self.user_id}_{self.task_id}.log"

        # 为当前线程创建一个标记过滤器
        filter_func = lambda record: thread_log_filter(record, self.user_id, self.task_id)

        # 添加一个新的文件handler，仅接收当前线程的日志消息
        self.logger_id = logger.add(log_file, filter=filter_func, rotation="20 MB",
                                    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

    def run(self):
        # 初始化日志
        if self.logger_id is None:
            self.setup_logger()
        thread_logger = logger.bind(user_id=self.user_id, task_id=self.task_id)
        self.thread_logger = thread_logger
        # 获取api信息
        acc = self.api()
        try:
            obj = RetryNetworkOperations(app.OkxSWAP(**acc))
        except:
            thread_logger.warning("停止交易，获取api信息失败，请重新提交api，并确认开启交易权限")
            return
        self.obj = obj
        # 根据api选择实盘还是模拟盘
        obj.account.api.flag = self.flag
        obj.trade.api.flag = self.flag
        thread_logger.info(f"跟单猿交易系统启动，跟随交易员：{self.uniqueName}")

        # okx源码被注释部分，先初始化账户开平仓模式
        set_position_mode_result = obj.account.set_position_mode(
            posMode='long_short_mode')
        if set_position_mode_result['code'] == '0':
            print('[SUCCESS] 设置持仓方式为双向持仓成功，posMode="long_short_mode"')
        else:
            print('[FAILURE] 设置持仓方式为双向持仓失败，请手动设置：posMode="long_short_mode"')
        self.perform_trade(obj, thread_logger)


    # 进数据库查api信息
    def api(self):
        with Connect() as conn:
            api_dict = conn.fetch_one("select flag,passPhrase,api_key,secret_key from api_apiinfo where id=%(id)s",
                                      id={self.api_id})
        self.flag = str(api_dict.get('flag'))
        acc = {
            'key': str(api_dict.get('api_key')),
            'secret': str(api_dict.get('secret_key')),
            'passphrase': str(api_dict.get('passPhrase')),
            'proxies': self.proxies()
        }
        return acc

    # 进数据库查询代理ip信息
    def proxies(self):
        with Connect() as conn:
            ip_dict = conn.fetch_one(
                "select username,password from api_ipinfo where user_id=%(user_id)s AND countdown>0",
                user_id={self.user_id})

            # 如果用户用模拟盘测试，但没有提供固定ip，则随机选择一个ip给用户使用
            if ip_dict is None and self.flag == '1':
                ip_dict = conn.fetch_one(
                    "select username,password from api_ipinfo where countdown>0")

            username = str(ip_dict.get('username'))
            password = str(ip_dict.get('password'))
            proxy = {
                'http': 'socks5h://{}:{}@{}:{}'.format(username, password, settings.PROXY_IP, settings.PROXY_PORT),
                'https': 'socks5h://{}:{}@{}:{}'.format(username, password, settings.PROXY_IP, settings.PROXY_PORT),
            }
        return proxy

    def update_data(self, new_data):
        self.task_id = new_data.get('task_id')
        self.order_type = new_data.get('order_type')
        self.trader_platform = new_data.get('trader_platform')
        self.uniqueName = new_data.get('uniqueName')
        self.follow_type = new_data.get('follow_type')
        self.sums = new_data.get('sums')
        self.lever_set = new_data.get('lever_set')
        self.first_order_set = new_data.get('first_order_set')
        self.api_id = new_data.get('api_id')
        self.user_id = new_data.get('user_id')
        self.availSubPos = new_data.get('availSubPos')
        self.old_availSubPos = new_data.get('old_availSubPos')
        self.new_availSubPos = new_data.get('new_availSubPos')
        self.instId = new_data.get('instId')
        self.mgnMode = new_data.get('mgnMode')
        self.posSide = new_data.get('posSide')
        self.lever = int(new_data.get('lever'))
        self.openTime = new_data.get('openTime')
        self.openAvgPx = new_data.get('openAvgPx')
        # 执行需要的操作
        self.perform_trade(self.obj, self.thread_logger)

    def perform_trade(self, obj, thread_logger):
        if not obj:
            print(f'{self.task_id} 错误')
            return
        if self.order_type == 'open':
            if self.posSide == 'net':
                # 解析订单方向
                number = int(self.availSubPos)
                if number > 0:
                    self.posSide = 'long'
                elif number < 0:
                    self.posSide = 'short'
            # 市价开仓
            obj.trade.open_market(instId=self.instId, posSide=self.posSide, openMoney=self.sums * 10, tdMode='cross',
                                  lever=self.lever)
            thread_logger.success(f'进行开仓操作，品种：{self.instId}，金额：{self.sums}USDT，方向：{self.posSide}')

        elif self.order_type == 'close':
            if self.posSide == 'net':
                # 解析订单方向
                number = int(self.availSubPos)
                if number > 0:
                    self.posSide = 'long'
                elif number < 0:
                    self.posSide = 'short'
            # 市价平仓
            obj.trade.close_market(instId=self.instId, posSide=self.posSide, quantityCT='all', tdMode='cross')
            thread_logger.success(f'进行平仓操作，品种:{self.instId}，方向：{self.posSide}')

        elif self.order_type == 'change':
            new_number = int(self.new_availSubPos)
            old_number = int(self.old_availSubPos)
            ratio = new_number / old_number  # 大于1是加仓，小于1是减仓
            if self.posSide == 'net':
                # 解析订单方向
                if new_number > 0:
                    self.posSide = 'long'
                elif new_number < 0:
                    self.posSide = 'short'
            # 加仓操作
            if ratio > 1:
                obj.trade.open_market(instId=self.instId, posSide=self.posSide, openMoney=self.sums * 10,
                                      tdMode='cross', lever=self.lever)
                thread_logger.success(f'进行加仓操作，品种：{self.instId}，加仓量：{self.sums}USDT，方向：{self.posSide}')
            # 减仓操作
            if ratio < 1:
                # 获取当前持仓，计算减仓量=当前*(1-ratio)
                try:
                    quantityCT = int(obj.account.get_positions(instId=self.instId, posSide=self.posSide).get('data')[0].get(
                        'availPos')) * (1 - ratio)
                except:
                    thread_logger.success(f'进行减仓操作，品种：{self.instId}，暂时没有仓位，继续跟单中...')
                    return
                obj.trade.close_market(instId=self.instId, posSide=self.posSide, quantityCT=quantityCT, tdMode='cross')
                percentage = "{:.2f}%".format((1 - ratio)*100)
                thread_logger.success(f'进行减仓操作，品种：{self.instId}，减仓量：{quantityCT}USDT，减仓占比：{percentage}')

    def stop(self):
        self.thread_logger.warning(f'手动结束跟单，结束跟单并不会平仓。如有正在进行中的交易，请及时手动在交易所平仓，避免资金损失！')


# 用字典映射任务ID和爬虫实例
traders = {}

if __name__ == '__main__':
    while True:
        try:
            # 去redis里获取跟单任务id
            conn = redis.Redis(**settings.REDIS_PARAMS)
            try:
                retrieved_json = conn.brpop(settings.TRADE_TASK_NAME, timeout=3)
            except:
                continue
            if not retrieved_json:
                continue
            retrieved_json = retrieved_json[1].decode('utf-8')
            retrieved_dict = json.loads(retrieved_json)  # 解析任务的字典

            print(retrieved_dict)
            status = retrieved_dict.get('status')
            task_id = retrieved_dict.get('task_id')

            if status is None:
                # 交易进程启动
                if task_id not in traders:
                    trader = Trader(**retrieved_dict)
                    trader.start()
                    traders[task_id] = trader
                    print(f"跟单任务{task_id}开始交易。")
                else:
                    # 在原有进程中直接进行交易
                    trader = traders[task_id]
                    trader.update_data(retrieved_dict)

            # 交易进程终止
            elif status == 2:
                if task_id in traders:
                    trader = traders.pop(task_id)
                    trader.stop()
                    trader.join()
                    print(f"跟单任务{task_id}已结束。")
                else:
                    print(f"跟单任务{task_id}不存在。")


        except (SyntaxError, NameError):
            print("数据错误！")
