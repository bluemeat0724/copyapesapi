from crawler.utils.db import Connect
from crawler.myokx import app
import threading
from crawler.utils.get_api import api
from crawler.utils.get_trade_times import get_trade_times
import time
from functools import wraps
from loguru import logger
from crawler.account.okx_orderinfo import OkxOrderInfo
import datetime
from crawler.account.update_quota import get_remaining_quota, check_task_pnl, update_remaining_quota

logger.remove()  # 移除所有默认的handler


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
    def __init__(self, task_id, api_id, user_id, trader_platform, uniqueName, follow_type, sums, lever_set,
                 first_order_set, posSide_set,
                 instId=None, mgnMode=None, posSide=None, lever=1, openTime=None, openAvgPx=None, margin=None,
                 availSubPos=None, order_type=None,
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
        self.posSide_set = posSide_set
        self.logger_id = None
        # self.thread_logger = None
        self.obj = None
        self.flag = None
        self.acc = None

    def log_to_database(self, level, title, description=""):
        """
        将日志信息保存到数据库。
        """
        params = {
            "user_id": self.user_id,
            "task_id": self.task_id,
            "date": datetime.datetime.now(),
            "color": level,
            "title": title,
            "description": description,
        }
        insert_sql = """
                        INSERT INTO api_tradelog (user_id, task_id, date, color, title, description, created_at, updated_at)
                        VALUES (%(user_id)s, %(task_id)s, %(date)s, %(color)s, %(title)s, %(description)s, NOW(), NOW())
                    """
        with Connect() as db:
            db.exec(insert_sql, **params)

    def run(self):
        # 获取api信息
        self.acc, self.flag = api(self.user_id, self.api_id)
        try:
            # 创建okx交易对象
            obj = RetryNetworkOperations(app.OkxSWAP(**self.acc))
            self.obj = obj

            # 根据api选择实盘还是模拟盘
            obj.account.api.flag = self.flag
            obj.trade.api.flag = self.flag
            # thread_logger.info(f"跟单猿交易系统启动，跟随交易员：{self.uniqueName}")
            self.log_to_database("INFO", f"跟单猿交易系统启动", f"跟随交易员：{self.uniqueName}")
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
            # thread_logger.WARNING("停止交易，获取api信息失败，请重新提交api，并确认开启交易权限")
            self.log_to_database("WARNING", "停止交易，获取api信息失败，请重新提交api，并确认开启交易权限")
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
        self.old_availSubPos = new_data.get('old_availSubPos')
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

    def change_pos_side_set(self, availSubPos):
        """
        :param availSubPos: availSubPos 值
        :return:
        """
        if availSubPos > 0:
            if int(self.posSide_set) == 1:
                self.posSide = 'long'
            else:
                self.posSide = 'short'
        elif availSubPos < 0:
            if int(self.posSide_set) == 1:
                self.posSide = 'short'
            else:
                self.posSide = 'long'
        return True

    # 执行okx交易
    def perform_trade(self):
        if not self.obj:
            print(f'{self.task_id} 错误')
            return
        if self.order_type == 'open':
            if self.posSide == 'net':
                # 解析订单方向
                self.change_pos_side_set(self.availSubPos)
            # 获取模拟盘/实盘交易倍数
            trade_times = get_trade_times(self.instId, self.flag, self.acc)
            if trade_times is None:
                # self.thread_logger.WARNING(f'模拟盘土狗币交易失败，品种：{self.instId}不在交易所模拟盘中！')
                self.log_to_database("WARNING", "模拟盘土狗币交易失败", f"品种：{self.instId}不在交易所模拟盘中！")
                return
            # 市价开仓
            print(f'时间：{datetime.datetime.now()}，用户id：{self.user_id}，任务id：{self.task_id}，品种：{self.instId}')
            result = self.obj.trade.open_market(instId=self.instId, posSide=self.posSide,
                                                openMoney=self.sums * trade_times, tdMode='cross',
                                                lever=self.lever)
            try:
                s_code_value = result.get('set_order_result', {}).get('data', {}).get('sCode')
                if s_code_value == '0':
                    self.log_to_database("success", "进行开仓操作", f"品种：{self.instId}，金额：{self.sums}USDT，方向：{self.posSide}")
                    # self.thread_logger.success(f'进行开仓操作，品种：{self.instId}，金额：{self.sums}USDT，方向：{self.posSide}')
            except:
                print(f'任务{self.task_id}错误信息：{result}')
                try:
                    s_code_value = result.get('set_order_result', {}).get('data', [{}])[0].get('sCode')
                    if s_code_value == '51000':
                        self.log_to_database("WARNING", '交易失败', '交易金额过低，请重新设置任务单笔跟单金额。')
                    elif s_code_value == '51010':
                        self.log_to_database("WARNING",
                                             '交易失败', '当前账户为简单交易模式，请在交易所合约交易页面进行手动调整。无需终止本次跟单任务，交易模式调整完成后，如有新的交易订单，将正常交易。')
                    elif s_code_value == '51008':
                        self.log_to_database("WARNING", '交易失败', '账户余额不足！请前往交易所充值！')
                    elif s_code_value == '51024':
                        self.log_to_database("WARNING", '交易失败', '交易账户冻结！请联系交易所客服处理！')
                    elif s_code_value in ['50103', '50104', '50105', '50106', '50107']:
                        self.log_to_database("WARNING", '交易失败', 'API信息填写错误，请结束任务后重新提交新的API！')
                    else:
                        self.log_to_database("WARNING",
                                             f'交易失败，请根据错误码，自行在官网https://www.okx.com/docs-v5/zh/?python#error-code查看错误原因。错误信息：{result}')
                except:
                    try:
                        s_code_value = result.get('error_result', {}).get('code')
                        if s_code_value == '51001':
                            self.log_to_database("WARNING", '模拟盘土狗币交易失败', f'品种：{self.instId}不在交易所模拟盘中！')
                        elif s_code_value == '59000':
                            self.log_to_database("WARNING", '设置失败', '请在设置前关闭任何挂单或持仓！')
                        else:
                            self.log_to_database("WARNING",
                                                 '交易失败', f'请根据错误码，自行在官网https://www.okx.com/docs-v5/zh/?python#error-code查看错误原因。错误信息：{result}')
                    except:
                        pass
        elif self.order_type == 'close':
            if self.posSide == 'net':
                # 解析订单方向
                self.change_pos_side_set(self.availSubPos)
            # 市价平仓
            print(f'时间：{datetime.datetime.now()}，用户id：{self.user_id}，任务id：{self.task_id}，品种：{self.instId}')
            self.obj.trade.close_market(instId=self.instId, posSide=self.posSide, quantityCT='all', tdMode='cross')
            # self.thread_logger.success(f'进行平仓操作，品种:{self.instId}，方向：{self.posSide}')
            self.log_to_database("success", f"进行平仓操作", f"品种:{self.instId}，方向：{self.posSide}")
            # 更新持仓数据
            # OkxOrderInfo(self.user_id, self.task_id).get_position()
            OkxOrderInfo(self.user_id, self.task_id).get_position_history(order_type=2)

        elif self.order_type == 'change':
            ratio = self.new_margin / self.old_margin  # 大于1是加仓，小于1是减仓
            if self.posSide == 'net':
                # 解析订单方向
                self.change_pos_side_set(self.new_availSubPos)
                # if self.new_availSubPos > 0:
                #     self.posSide = 'long'
                # elif self.new_availSubPos < 0:
                #     self.posSide = 'short'

            # 获取模拟盘/实盘交易倍数
            trade_times = get_trade_times(self.instId, self.flag, self.acc)
            if trade_times is None:
                self.log_to_database("WARNING", '模拟盘土狗币交易失败', f'品种：{self.instId}不在交易所模拟盘中！')
                return
            # 加仓操作
            if ratio > 1:
                print(f'时间：{datetime.datetime.now()}，用户id：{self.user_id}，任务id：{self.task_id}，品种：{self.instId}')
                result = self.obj.trade.open_market(instId=self.instId, posSide=self.posSide,
                                                    openMoney=self.sums * trade_times,
                                                    tdMode='cross', lever=self.lever)
                try:
                    s_code_value = result.get('set_order_result', {}).get('data', {}).get('sCode')
                    if s_code_value == '0':
                        self.log_to_database("success", '进行加仓操作', f'品种：{self.instId}，金额：{self.sums}USDT，方向：{self.posSide}')
                except:
                    print(f'任务{self.task_id}错误信息：{result}')
                    self.handle_trade_failure(result)

            # 减仓操作
            if ratio < 1:
                # 获取当前持仓，计算减仓量=当前*(1-ratio)
                try:
                    quantityCT = int(
                        self.obj.account.get_positions(instId=self.instId, posSide=self.posSide).get('data')[0].get(
                            'availPos')) * (1 - ratio)
                except:
                    self.log_to_database("success", '进行减仓操作', f'品种：{self.instId}，暂时没有仓位，继续跟单中...')
                    return
                print(f'时间：{datetime.datetime.now()}，用户id：{self.user_id}，任务id：{self.task_id}，品种：{self.instId}')
                self.obj.trade.close_market(instId=self.instId, posSide=self.posSide, quantityCT=quantityCT,
                                            tdMode='cross')
                # 更新持仓数据
                OkxOrderInfo(self.user_id, self.task_id).get_position_history(order_type=1)
                percentage = "{:.2f}%".format((1 - ratio) * 100)
                self.log_to_database("success", '进行减仓操作', f'品种：{self.instId}，减仓占比：{percentage}')

    def handle_trade_failure(self, result):
        try:
            s_code_value = result.get('set_order_result', {}).get('data', [{}])[0].get('sCode')
            if s_code_value == '51000':
                self.log_to_database("WARNING", '交易失败', '交易金额过低，请重新设置任务单笔跟单金额。')
            elif s_code_value == '51010':
                self.log_to_database("WARNING",
                                     '交易失败', '当前账户为简单交易模式，请在交易所合约交易页面进行手动调整。无需终止本次跟单任务，交易模式调整完成后，如有新的交易订单，将正常交易。')
            elif s_code_value == '51008':
                self.log_to_database("WARNING", '交易失败', '账户余额不足！请前往交易所充值！')
            elif s_code_value == '51024':
                self.log_to_database("WARNING", '交易失败', '交易账户冻结！请联系交易所客服处理！')
            elif s_code_value in ['50103', '50104', '50105', '50106', '50107']:
                self.log_to_database("WARNING", '交易失败', 'API信息填写错误，请结束任务后重新提交新的API！')
            else:
                self.log_to_database("WARNING",
                                     '交易失败', f'请根据错误码，自行在官网https://www.okx.com/docs-v5/zh/?python#error-code查看错误原因。错误信息：{result}')
        except:
            try:
                s_code_value = result.get('error_result', {}).get('code')
                if s_code_value == '51001':
                    self.log_to_database("WARNING", '模拟盘土狗币交易失败', f'品种：{self.instId}不在交易所模拟盘中！')
                elif s_code_value == '59000':
                    self.log_to_database("WARNING", '设置失败', '请在设置前关闭任何挂单或持仓！')
                else:
                    self.log_to_database("WARNING",
                                         '交易失败', f'请根据错误码，自行在官网https://www.okx.com/docs-v5/zh/?python#error-code查看错误原因。错误信息：{result}')
            except:
                pass

    # 手动结束跟单，打印日志
    def stop(self):
        # 结束全部正在进行中的交易
        try:
            data = self.obj.account.get_positions().get('data')
        except:
            return
        if not data:
            # # 账户获取剩余额度
            # remaining_quota = get_remaining_quota(self.user_id, int(self.flag))
            # # 获取任务收益
            # task_pnl = check_task_pnl(self.task_id)
            # remaining_quota -= task_pnl
            # # 更新剩余额度数据
            # update_remaining_quota(self.user_id, int(self.flag), remaining_quota)
            #
            # print(f'更新用户{self.user_id}可用盈利额度数据成功！')
            # 打印日志
            self.log_to_database("WARNING", '手动结束跟单', f'任务：{self.task_id}')
            return
        for item in data:
            instId = item.get('instId')
            posSide = item.get('posSide')
            # 市价平仓
            self.obj.trade.close_market(instId=instId, posSide=posSide, quantityCT='all', tdMode='cross')
            self.log_to_database("WARNING", '手动结束跟单', f'{instId}已经按市价进行平仓。')

        # 更新收益数据，以及对应可用额度数据
        OkxOrderInfo(self.user_id, self.task_id).get_position_history(order_type=2)

        # # 账户获取剩余额度
        # remaining_quota = get_remaining_quota(self.user_id, int(self.flag))
        # # 获取任务收益
        # task_pnl = check_task_pnl(self.task_id)
        # remaining_quota -= task_pnl
        # # 更新剩余额度数据
        # update_remaining_quota(self.user_id, int(self.flag), remaining_quota)
        #
        # print(f'更新用户{self.user_id}可用盈利额度数据成功！')
        self.log_to_database("WARNING", f'手动结束跟单，任务：{self.task_id}')
