from crawler.myokx import app
import threading
from crawler.utils.get_api import api
from crawler.utils.get_trade_times import get_trade_times
import time
from functools import wraps
from loguru import logger
import os
from crawler.account.okx_orderinfo import OkxOrderInfo
import datetime


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
    def __init__(self, task_id, api_id,user_id, trader_platform, uniqueName, follow_type, sums, lever_set, first_order_set,
                 instId=None, mgnMode=None, posSide=None, lever=1, openTime=None, openAvgPx=None, margin=None,availSubPos=None,order_type=None,
                 old_margin=None, new_margin=None, old_availSubPos=None, new_availSubPos=None):
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
        self.margin = margin
        self.availSubPos = availSubPos
        self.old_margin = old_margin
        self.old_availSubPos = old_availSubPos
        self.new_margin = new_margin
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
        self.acc = None

    def setup_logger(self):
        # log_file = f"trade_logs/{self.user_id}_{self.task_id}.log"
        log_file = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "trade_logs",
                                                f"{self.user_id}_{self.task_id}.log"))
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
        self.acc, self.flag = api(self.user_id, self.api_id)
        try:
            # 创建okx交易对象
            obj = RetryNetworkOperations(app.OkxSWAP(**self.acc))
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
            self.perform_trade()
        except Exception as e:
            print(f"交易失败，原因: {e}")
            thread_logger.warning("停止交易，获取api信息失败，请重新提交api，并确认开启交易权限")
            return

    # 更新交易数据，执行最新交易
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
        self.margin = new_data.get('margin')
        self.availSubPos = new_data.get('availSubPos')
        self.old_margin = new_data.get('old_margin')
        self.old_availSubPos= new_data.get('old_availSubPos')
        self.new_margin = new_data.get('new_margin')
        self.new_availSubPos = new_data.get('new_availSubPos')
        self.instId = new_data.get('instId')
        self.mgnMode = new_data.get('mgnMode')
        self.posSide = new_data.get('posSide')
        self.lever = int(new_data.get('lever'))
        self.openTime = new_data.get('openTime')
        self.openAvgPx = new_data.get('openAvgPx')
        # 执行需要的操作
        self.perform_trade()

    # 执行okx交易
    def perform_trade(self):
        if not self.obj:
            print(f'{self.task_id} 错误')
            return
        if self.order_type == 'open':
            if self.posSide == 'net':
                # 解析订单方向
                if self.availSubPos > 0:
                    self.posSide = 'long'
                elif self.availSubPos < 0:
                    self.posSide = 'short'
            # 获取模拟盘/实盘交易倍数
            trade_times = get_trade_times(self.instId, self.flag, self.acc)
            if trade_times is None:
                self.thread_logger.warning(f'模拟盘土狗币交易失败，品种：{self.instId}不在交易所模拟盘中！')
                return
            # 市价开仓
            print(f'时间：{datetime.datetime.now()}，用户id：{self.user_id}，任务id：{self.task_id}，品种：{self.instId}')
            result = self.obj.trade.open_market(instId=self.instId, posSide=self.posSide, openMoney=self.sums * trade_times, tdMode='cross',
                                  lever=self.lever)
            try:
                s_code_value = result.get('set_order_result', {}).get('data', {}).get('sCode')
                if s_code_value == '0':
                    self.thread_logger.success(f'进行开仓操作，品种：{self.instId}，金额：{self.sums}USDT，方向：{self.posSide}')
            except Exception as e:
                print(e)
                try:
                    s_code_value = result.get('set_order_result', {}).get('data', [{}])[0].get('sCode')
                    if s_code_value == '51010':
                        self.thread_logger.warning(
                            f'交易失败，当前账户为简单交易模式，请在交易所合约交易页面进行手动调整。无需终止本次跟单任务，交易模式调整完成后，如有新的交易订单，将正常交易。')
                    if s_code_value == '51008':
                        self.thread_logger.warning('交易失败，账户余额不足！请前往交易所充值！')
                    if s_code_value == '51024':
                        self.thread_logger.warning('交易失败，交易账户冻结！请联系交易所客服处理！')
                    if s_code_value in ['50103','50104','50105','50106','50107']:
                        self.thread_logger.warning('交易失败，API信息填写错误，请结束任务后重新提交新的API！')
                except:
                    try:
                        s_code_value = result.get('error_result', {}).get('code')
                        if s_code_value == '51001':
                            self.thread_logger.warning(f'模拟盘土狗币交易失败，品种：{self.instId}不在交易所模拟盘中！')
                    except:
                        self.thread_logger.warning(f'交易失败，错误信息：{e}')

        elif self.order_type == 'close':
            if self.posSide == 'net':
                # 解析订单方向
                if self.availSubPos > 0:
                    self.posSide = 'long'
                elif self.availSubPos < 0:
                    self.posSide = 'short'
            # 市价平仓
            print(f'时间：{datetime.datetime.now()}，用户id：{self.user_id}，任务id：{self.task_id}，品种：{self.instId}')
            self.obj.trade.close_market(instId=self.instId, posSide=self.posSide, quantityCT='all', tdMode='cross')
            self.thread_logger.success(f'进行平仓操作，品种:{self.instId}，方向：{self.posSide}')
            # 更新持仓数据
            OkxOrderInfo(self.user_id, self.task_id).get_position()
            # OkxOrderInfo(self.user_id, self.task_id).get_position_history()

        elif self.order_type == 'change':
            ratio = self.new_margin / self.old_margin  # 大于1是加仓，小于1是减仓
            if self.posSide == 'net':
                # 解析订单方向
                if self.new_availSubPos > 0:
                    self.posSide = 'long'
                elif self.new_availSubPos < 0:
                    self.posSide = 'short'

            # 获取模拟盘/实盘交易倍数
            trade_times = get_trade_times(self.instId, self.flag, self.acc)
            if trade_times is None:
                self.thread_logger.warning(f'模拟盘土狗币交易失败，品种：{self.instId}不在交易所模拟盘中！')
                return
            # 加仓操作
            if ratio > 1:
                print(f'时间：{datetime.datetime.now()}，用户id：{self.user_id}，任务id：{self.task_id}，品种：{self.instId}')
                result = self.obj.trade.open_market(instId=self.instId, posSide=self.posSide, openMoney=self.sums * trade_times,
                                      tdMode='cross', lever=self.lever)
                try:
                    s_code_value = result.get('set_order_result', {}).get('data', {}).get('sCode')
                    if s_code_value == '0':
                        self.thread_logger.success(f'进行加仓操作，品种：{self.instId}，金额：{self.sums}USDT，方向：{self.posSide}')
                except Exception as e:
                    print(e)
                    try:
                        s_code_value = result.get('set_order_result', {}).get('data', [{}])[0].get('sCode')
                        if s_code_value == '51010':
                            self.thread_logger.warning(
                                '交易失败，当前账户为简单交易模式，请在交易所合约交易页面进行手动调整。无需终止本次跟单任务，交易模式调整完成后，如有新的交易订单，将正常交易。')
                        if s_code_value == '51008':
                            self.thread_logger.warning('交易失败，账户余额不足！请前往交易所充值！')
                        if s_code_value == '51024':
                            self.thread_logger.warning('交易失败，交易账户冻结！请联系交易所客服处理！')
                        if s_code_value in ['50103', '50104', '50105', '50106', '50107']:
                            self.thread_logger.warning('交易失败，API信息填写错误，请结束任务后重新提交新的API！')
                    except:
                        try:
                            s_code_value = result.get('error_result', {}).get('code')
                            if s_code_value == '51001':
                                self.thread_logger.warning(f'模拟盘土狗币交易失败，品种：{self.instId}不在交易所模拟盘中！')
                        except:
                            self.thread_logger.warning(f'交易失败，错误信息：{e}')

            # 减仓操作
            if ratio < 1:
                # 获取当前持仓，计算减仓量=当前*(1-ratio)
                try:
                    quantityCT = int(self.obj.account.get_positions(instId=self.instId, posSide=self.posSide).get('data')[0].get(
                        'availPos')) * (1 - ratio)
                except:
                    self.thread_logger.success(f'进行减仓操作，品种：{self.instId}，暂时没有仓位，继续跟单中...')
                    return
                print(f'时间：{datetime.datetime.now()}，用户id：{self.user_id}，任务id：{self.task_id}，品种：{self.instId}')
                self.obj.trade.close_market(instId=self.instId, posSide=self.posSide, quantityCT=quantityCT, tdMode='cross')
                # 更新持仓数据
                OkxOrderInfo(self.user_id, self.task_id).get_position_history(order_type=1)
                percentage = "{:.2f}%".format((1 - ratio)*100)
                self.thread_logger.success(f'进行减仓操作，品种：{self.instId}，减仓占比：{percentage}')

    # 手动结束跟单，打印日志
    def stop(self):
        # 结束全部正在进行中的交易
        try:
            data = self.obj.account.get_positions().get('data')
        except:
            return
        if not data:
            # 打印日志
            self.thread_logger.warning(f'手动结束跟单，任务：{self.task_id}')
            return
        for item in data:
            instId = item.get('instId')
            posSide = item.get('posSide')
            # 市价平仓
            self.obj.trade.close_market(instId=instId, posSide=posSide, quantityCT='all', tdMode='cross')
            self.thread_logger.warning(f'手动结束跟单，{instId}已经按市价进行平仓。')

        # 更新收益数据，以及对应可用额度数据
        OkxOrderInfo(self.user_id, self.task_id).get_position_history(order_type=2)
        print(f'用户{self.user_id}任务{self.task_id}更新持仓数据')
        self.thread_logger.warning(f'手动结束跟单，任务：{self.task_id}')




