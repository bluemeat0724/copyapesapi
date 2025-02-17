import uuid
from crawler.settingsprod import HOST_IP
from crawler.utils.db import Connect
from crawler.myokx import app
import threading
from crawler.utils.get_api import api
from crawler.utils.push_tool import Push
from crawler.utils.get_trade_times import get_trade_times
import re
import time
from crawler.account.okx_orderinfo import OkxOrderInfo
import datetime
from concurrent.futures import ThreadPoolExecutor
from crawler.account.update_quota import get_remaining_quota, check_task_pnl, update_remaining_quota


class Trader(threading.Thread):
    def __init__(self, task_id, api_id, user_id, trader_platform, uniqueName, follow_type, role_type, reduce_ratio,
                 sums, ratio, lever_set,
                 first_order_set, posSide_set, investment, trade_trigger_mode, sl_trigger_px, tp_trigger_px,
                 instId=None, mgnMode=None, posSide=None, lever=1, openTime=None, openAvgPx=None, margin=None,
                 availSubPos=None, order_type=None,
                 old_margin=None, new_margin=None, old_availSubPos=None, new_availSubPos=None, status=None,
                 fast_mode=0):
        super(Trader, self).__init__()
        self.task_id = task_id
        self.order_type = order_type
        self.trader_platform = trader_platform
        self.uniqueName = uniqueName
        self.follow_type = follow_type
        self.role_type = role_type
        self.reduce_ratio = reduce_ratio
        self.sums = sums
        self.ratio = ratio
        self.lever_set = lever_set
        self.investment = investment
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
        self.lever = float(lever)
        self.openTime = openTime
        self.posSide_set = posSide_set
        self.logger_id = None
        self.obj = None
        self.flag = None
        self.acc = None
        self.ip_id = None
        self.status = None
        self.fast_mode = fast_mode

        # 止盈/损模块 是否开启
        self.trade_trigger_mode = trade_trigger_mode
        # 止损比例
        self.sl_trigger_px = float(sl_trigger_px) / 100
        # 止盈比例
        self.tp_trigger_px = float(tp_trigger_px) / 100
        # 跟单用户开仓均价
        self.openAvgPx = openAvgPx

    def log_to_database(self, level, title, description=""):
        """
        将日志信息保存到数据库。
        """
        params = {
            "user_id": self.user_id,
            "task_id": self.task_id,
            "color": level,
            "title": title,
            "description": description,
        }
        insert_sql = """
                        INSERT INTO api_tradelog (user_id, task_id, date, color, title, description, created_at, updated_at)
                        VALUES (%(user_id)s, %(task_id)s, NOW(), %(color)s, %(title)s, %(description)s, NOW(), NOW())
                    """
        with Connect() as db:
            db.exec(insert_sql, **params)

    def run(self):
        # 获取api信息
        self.acc, self.flag, self.ip_id = api(self.user_id, self.api_id)
        if int(self.fast_mode) == 1:
            res = self.check_ip()
            if res:
                self.acc.pop("proxies")
        try:
            self.write_task_log()
            # update task 里面的 ip_id
            self.update_task_with_ip()
            # 创建okx交易对象
            obj = app.OkxSWAP(**self.acc)
            self.obj = obj

            # 根据api选择实盘还是模拟盘
            obj.account.api.flag = self.flag
            obj.trade.api.flag = self.flag
            # thread_logger.info(f"跟单猿交易系统启动，跟随交易员：{self.uniqueName}")
            obj.account.set_position_mode(posMode='long_short_mode')
            # okx源码被注释部分，先初始化账户开平仓模式
            # set_position_mode_result = obj.account.set_position_mode(
            #     posMode='long_short_mode')
            # if set_position_mode_result['code'] == '0':
            #     print('[SUCCESS] 设置持仓方式为双向持仓成功，posMode="long_short_mode"')
            # else:
            #     print('[FAILURE] 设置持仓方式为双向持仓失败，请手动设置：posMode="long_short_mode"')
        except Exception as e:
            print(f"{self.task_id}交易失败，原因: {e}")
            match = re.search(r'"code":"(\d+)"', str(e))
            if match:
                code_value = match.group(1)
                if code_value == '50101':
                    self.log_to_database("WARNING", "停止交易", "请确认APIKEY和实盘或者模拟盘环境匹配！")
                elif code_value == '50105':
                    self.log_to_database("WARNING", 'API错误', 'PASSPHRASE填写错误，请结束任务，重新提交！')
                elif code_value == '50001':
                    self.log_to_database("WARNING", '交易所服务错误', '交易所服务暂时不可用，请稍后重试！')
            # thread_logger.WARNING("停止交易，获取api信息失败，请重新提交api，并确认开启交易权限")
            # self.log_to_database("WARNING", "停止交易", "请确认APIKEY和实盘或者模拟盘环境匹配！")
            return
        self.perform_trade()

    def change_pos_side_set(self, availSubPos):
        """
        :param availSubPos: availSubPos 值
        :return:
        """
        if self.posSide == 'long':
            if int(self.posSide_set) == 2:
                self.posSide = 'short'
        elif self.posSide == 'short':
            if int(self.posSide_set) == 2:
                self.posSide = 'long'
        elif self.posSide == 'net':
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

    def get_sl_trigger_px(self) -> str:
        """
        获取止损价格
        """
        _re_try = 0
        open_price = 0
        while _re_try < 3 and open_price == 0:
            _re_try += 1
            try:
                get_ticker_result = self.obj.trade._market.get_ticker(instId=self.instId)
                # 获取市价
                open_price = float(get_ticker_result['data']['askPx'])
            except:
                continue
        # 根据 开仓价格 & 杠杆 & 方向 获取止损挂单价
        # 开空
        if self.posSide == "short":
            # 止损价格 = 开仓价格 * (1 - 止损未亏损比例)
            # _sl_price = (1 + self.sl_trigger_px) * open_price
            # 平仓止损挂单价格 = 开仓价格 + （（开仓价格 - 止损价格） / 杠杆倍数）
            # sl_trigger_px_price = open_price + (open_price - ((open_price - _sl_price) / self.lever))
            # 止损比例转化为币价涨幅比例
            _r = self.sl_trigger_px / self.lever
            # 止损挂单价格 = 开仓价格 *（ 1+ _r ）
            sl_trigger_px_price = open_price * (1 + _r)
            sl_trigger_px_price = f"{sl_trigger_px_price:.150f}"
        # 开多
        elif self.posSide == "long":
            # 止损价格 = 开仓价格 * (1 - 止损未亏损比例)
            # _sl_price = (1 - self.sl_trigger_px) * open_price
            # 平仓止损挂单价格 = 开仓价格 - （（开仓价格 - 止损价格） / 杠杆倍数）
            # sl_trigger_px_price = open_price - (open_price - ((open_price - _sl_price) / self.lever))
            # 止损比例转化为币价涨幅比例
            _r = self.sl_trigger_px / self.lever
            # 止损挂单价格 = 开仓价格 *（ 1 - _r ）
            sl_trigger_px_price = open_price * (1 - _r)
            sl_trigger_px_price = f"{sl_trigger_px_price:.150f}"
        else:
            raise ValueError("posSide参数错误")
        return sl_trigger_px_price.rstrip("0")

    def get_tp_trigger_px(self) -> str:
        """
        获取止盈价格
        """
        _re_try = 0
        open_price = 0
        while _re_try < 3 and open_price == 0:
            _re_try += 1
            try:
                get_ticker_result = self.obj.trade._market.get_ticker(instId=self.instId)
                # 获取市价
                open_price = float(get_ticker_result['data']['askPx'])
            except:
                continue
       
        # 根据 开仓价格 & 杠杆 & 方向 获取止损挂单价
        # 开多
        if self.posSide == "long":
            # 止盈价格 = 开仓价格 * (1 - 止损未亏损比例)
            # _tp_price = (1 + self.tp_trigger_px) * open_price
            # 平仓止损挂单价格 = 开仓价格 + （（开仓价格 - 止盈价格 / 杠杆倍数）
            # tp_trigger_px_price = open_price + (open_price - ((open_price - _tp_price) / self.lever))
            # 止盈比例转化为币价涨幅比例
            _r = self.tp_trigger_px / self.lever
            # 止盈挂单价格 = 开仓价格 *（ 1 + _r ）
            tp_trigger_px_price = open_price * (1 + _r)
            tp_trigger_px_price = f"{tp_trigger_px_price:.150f}"
        # 开空
        elif self.posSide == "short":
            # 止损价格 = 开仓价格 * (1 - 止损未亏损比例)
            # _tp_price = (1 - self.tp_trigger_px) * open_price
            # 平仓止损挂单价格 = 开仓价格 - （（开仓价格 - 止损价格） / 杠杆倍数）
            # tp_trigger_px_price = open_price - (open_price - ((open_price - _tp_price) / self.lever))
            # 止盈比例转化为币价涨幅比例
            _r = self.tp_trigger_px / self.lever
            # 止盈挂单价格 = 开仓价格 *（ 1 - _r ）
            tp_trigger_px_price = open_price * (1 - _r)
            tp_trigger_px_price = f"{tp_trigger_px_price:.150f}"
        else:
            raise ValueError("posSide参数错误")
        return tp_trigger_px_price.rstrip("0")

    # 执行okx交易
    def perform_trade(self):
        if not self.obj:
            print(f'{self.task_id} 错误')
            return
        # 仓位变动操作
        if self.follow_type == 2:
            self.transform_sums()
        # 开仓操作
        if self.order_type == 'open':
            # 解析订单方向
            self.change_pos_side_set(self.availSubPos)
            # 获取模拟盘/实盘交易倍数
            trade_times = get_trade_times(self.instId, self.flag, self.acc)
            if trade_times is None:
                self.log_to_database("WARNING", "模拟盘土狗币交易失败", f"品种：{self.instId}不在交易所模拟盘中！")
                return
            # 市价开仓
            time_now = datetime.datetime.now()
            print(f'时间：{time_now}，用户id：{self.user_id}，任务id：{self.task_id}，品种：{self.instId}')
            # 开单总金额
            open_total_money = self.sums * trade_times
            params = dict(
                instId=self.instId,
                posSide=self.posSide,
                openMoney=open_total_money,
                tdMode=self.mgnMode,
                lever=self.lever)
            # 增加止损
            if self.trade_trigger_mode and self.sl_trigger_px:
                _sl_price = self.get_sl_trigger_px()
                params.update({"slTriggerPx": _sl_price})
                params.update({"slOrdPx": _sl_price})
                print(
                    f'时间：{time_now}，用户id：{self.user_id}，任务id：{self.task_id}，品种：{self.instId}，止损触发：{self.get_sl_trigger_px()}')
            # 增加止盈
            if self.trade_trigger_mode and self.tp_trigger_px:
                _tp_price = self.get_tp_trigger_px()
                params.update({"tpTriggerPx": _tp_price})
                params.update({"tpOrdPx": _tp_price})
                print(
                    f'时间：{time_now}，用户id：{self.user_id}，任务id：{self.task_id}，品种：{self.instId}，止盈触发：{self.get_tp_trigger_px()}')

            result = self.obj.trade.open_market(**params)
            try:
                s_code_value = result.get('set_order_result', {}).get('data', {}).get('sCode')
                if s_code_value == '0':
                    title = "进行开仓操作"
                    content = f"品种：{self.instId}，金额：{self.sums}USDT，方向：{self.posSide}"
                    self.log_to_database("success", title, content)
                    Push(self.user_id, self.task_id, time_now, self.instId, self.posSide, self.lever, self.order_type, subject=title, body=content).push()
                    # self.thread_logger.success(f'进行开仓操作，品种：{self.instId}，金额：{self.sums}USDT，方向：{self.posSide}')
            except:
                print(f'任务{self.task_id}错误信息：{result}')
                self.handle_trade_failure(result)


        elif self.order_type == 'close':
            # 解析订单方向
            self.change_pos_side_set(self.availSubPos)
            # 市价平仓
            time_now = datetime.datetime.now()
            print(f'时间：{time_now}，用户id：{self.user_id}，任务id：{self.task_id}，品种：{self.instId}')
            # res = self.obj.trade.close_market(instId=self.instId, posSide=self.posSide, quantityCT='all',
            #                                   tdMode=self.mgnMode)
            clOrdId = uuid.uuid4().hex
            res = self.obj.trade.set_close_position(instId=self.instId, posSide=self.posSide, mgnMode=self.mgnMode, autoCxl=True, clOrdId=clOrdId)
            print(f'{self.task_id}###{res}')

            if res.get('code') == '0' and res.get('data')[0].get("clOrdId") == clOrdId:
                title = "进行平仓操作"
                content = f"品种：{self.instId}，方向：{self.posSide}"
                self.log_to_database("success", title, content)
                Push(self.user_id, self.task_id, time_now, self.instId, self.posSide, self.lever, self.order_type, subject=title, body=content).push()
            elif res.get('code') in ['51001', '51023']:
                self.log_to_database("success", f"进行平仓操作", f"品种:{self.instId}仓位不存在")
            else:
                # 平仓出错，拆分平仓
                print(f'任务：{self.task_id}平仓出错，拆分平仓！')
                market_data = self.close_market_2nd()
                if market_data:
                    self.run_close_market_concurrently(market_data)

            # self.thread_logger.success(f'进行平仓操作，品种:{self.instId}，方向：{self.posSide}')
            # self.log_to_database("success", f"进行平仓操作", f"品种:{self.instId}，方向：{self.posSide}")
            # 更新持仓数据
            # OkxOrderInfo(self.user_id, self.task_id).get_position()
            OkxOrderInfo(self.user_id, self.task_id).get_position_history(order_type=2)

        elif self.order_type == 'change':
            ratio = self.new_margin / self.old_margin  # 大于1是加仓，小于1是减仓
            # 解析订单方向
            self.change_pos_side_set(self.new_availSubPos)

            # 获取模拟盘/实盘交易倍数
            trade_times = get_trade_times(self.instId, self.flag, self.acc)
            if trade_times is None:
                self.log_to_database("WARNING", '模拟盘土狗币交易失败', f'品种：{self.instId}不在交易所模拟盘中！')
                return
            # 加仓操作
            time_now = datetime.datetime.now()
            if ratio > 1:
                print(f'时间：{time_now}，用户id：{self.user_id}，任务id：{self.task_id}，品种：{self.instId}')
                result = self.obj.trade.open_market(instId=self.instId, posSide=self.posSide,
                                                    openMoney=self.sums * trade_times,
                                                    tdMode=self.mgnMode, lever=self.lever)
                try:
                    s_code_value = result.get('set_order_result', {}).get('data', {}).get('sCode')
                    if s_code_value == '0':
                        title = "进行加仓操作"
                        content = f"品种：{self.instId}，金额：{self.sums}USDT，方向：{self.posSide}"
                        self.log_to_database("success", title, content)
                        Push(self.user_id, self.task_id, time_now, self.instId, self.posSide, self.lever, 'open', subject=title, body=content).push()
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
                print(f'时间：{time_now}，用户id：{self.user_id}，任务id：{self.task_id}，品种：{self.instId}')
                self.obj.trade.close_market(instId=self.instId, posSide=self.posSide, quantityCT=quantityCT,
                                            tdMode=self.mgnMode)
                percentage = "{:.2f}%".format((1 - ratio) * 100)
                title = "进行减仓操作"
                content = f"品种：{self.instId}，减仓占比：{percentage}"
                self.log_to_database("success", title, content)
                Push(self.user_id, self.task_id, time_now, self.instId, self.posSide, self.lever, f'close({percentage})', subject=title, body=content).push()
                # 更新持仓数据
                OkxOrderInfo(self.user_id, self.task_id).get_position_history(order_type=1)

        # 跟单普通用户发生减仓操作
        elif self.order_type == 'reduce':
            # 解析订单方向
            self.change_pos_side_set(self.new_availSubPos)
            if self.follow_type == 1:
                # 获取当前持仓，计算减仓量=当前*self.reduce_ratio
                try:
                    quantityCT = float(
                        self.obj.account.get_positions(instId=self.instId, posSide=self.posSide).get('data')[0].get(
                            'availPos')) * self.reduce_ratio
                except:
                    self.log_to_database("success", '进行减仓操作', f'品种：{self.instId}，暂时没有仓位，继续跟单中...')
                    return
            else:
                if self.sums == 0:
                    self.log_to_database("success", '进行减仓操作', f'品种：{self.instId}，暂时没有仓位，继续跟单中...')
                    return
                elif self.sums < 0:
                    self.log_to_database("success", '进行减仓操作', f'品种：{self.instId}，当前仓位小于交易员仓位比例，无需减仓！')
                    return
                # 按仓位比例跟单，将减仓金额转换为张数
                trade_times = get_trade_times(self.instId, self.flag, self.acc)
                if trade_times is None:
                    self.log_to_database("WARNING", "模拟盘土狗币交易失败", f"品种：{self.instId}不在交易所模拟盘中！")
                    return
                get_ticker_result = self.obj.trade._market.get_ticker(instId=self.instId)
                openPrice = float(get_ticker_result['data']['askPx'])
                quantityCT = self.obj.trade.get_quantity(
                    openPrice=openPrice, openMoney=self.sums * trade_times,
                    instId=self.instId, ordType='market',
                    leverage=self.lever,
                ).get('data')
            time_now = datetime.datetime.now()
            print(f'时间：{time_now}，用户id：{self.user_id}，任务id：{self.task_id}，品种：{self.instId}')
            self.obj.trade.close_market(instId=self.instId, posSide=self.posSide, quantityCT=quantityCT,
                                        tdMode=self.mgnMode)
            if self.follow_type == 1:
                percentage = "{:.2f}%".format(self.reduce_ratio * 100)
                title = "进行减仓操作"
                content = f"品种：{self.instId}，减仓占比：{percentage}"
                self.log_to_database("success", title, content)
                Push(self.user_id, self.task_id, time_now, self.instId, self.posSide, self.lever, f'close({percentage})', subject=title, body=content).push()
            else:
                title = "进行减仓操作"
                content = f"品种：{self.instId}，减仓保证金：{self.sums}USDT"
                self.log_to_database("success", title, content)
                Push(self.user_id, self.task_id, time_now, self.instId, self.posSide, self.lever, f'close({self.sums}USDT)', subject=title, body=content).push()
            # 更新持仓数据
            OkxOrderInfo(self.user_id, self.task_id).get_position_history(order_type=1)
        elif self.order_type == 'close_all':
            # 结束全部正在进行中的交易
            data = self.obj.account.get_positions().get('data')
            market_data = []
            for item in data:
                market_data.append(
                    dict(
                        instId=item.get('instId'),
                        posSide=item.get('posSide'),
                        mgnMode=item.get('mgnMode'),
                        order_type='close_all'
                    )
                )
                print(f"时间：{datetime.datetime.now()}，用户id：{self.user_id}，任务id：{self.task_id}，品种：{item.get('instId')}")
            if market_data:
                self.run_close_market_concurrently(market_data)
            OkxOrderInfo(self.user_id, self.task_id).get_position_history(order_type=2)

    def handle_trade_failure(self, result):
        try:
            s_code_value = result.get('set_order_result', {}).get('data', [{}])[0].get('sCode')
            if s_code_value == '51000':
                content = '交易金额过低，请重新设置任务单笔跟单金额。如果是智能跟单模式，当前仓位大于交易员仓位比例，本次不进行交易。'
            elif s_code_value == '51010':
                content = '当前账户为全仓模式，请在交易所合约交易页面进行手动调整。无需终止本次跟单任务，交易模式调整完成后，如有新的交易订单，将正常交易。'
            elif s_code_value == '51008':
                content = '账户余额不足！请前往交易所充值！'
            elif s_code_value == '51169':
                content = '下单失败，当前合约无持仓！'
            elif s_code_value == '51202':
                content = '市价单下单数量超出最大值！'
            elif s_code_value == '51024':
                content = '交易账户冻结！请联系交易所客服处理！'
            elif s_code_value == '51004':
                content = '当前下单张数、多空持有仓位以及多空挂单张数之和，不能超过当前杠杆倍数允许的持仓上限。请调低杠杆或者使用新的子账户重新下单'
            elif s_code_value == '50013':
                content = '交易所系统繁忙，导致交易失败。本次交易放弃。'
            elif s_code_value == '51202':
                content = '市价单下单数量超出最大值。本次交易放弃。如果当前为模拟盘跟单，出现该错误为正常现象，不会影响实盘跟单。'
            elif s_code_value in ['50103', '50104', '50105', '50106', '50107']:
                content = 'API信息填写错误，请结束任务后重新提交新的API！'
            else:
                content = f'请根据错误码（sCord），自行在官网https://www.okx.com/docs-v5/zh/?python#error-code查看错误原因。错误信息：{result}'

            self.log_to_database("WARNING", '交易失败', content)
            Push(self.user_id, self.task_id, datetime.datetime.now(), self.instId, self.posSide, self.lever, f'开仓失败（sCord:{s_code_value}）', subject='交易失败', body=content).push()
        except:
            try:
                s_code_value = result.get('error_result', {}).get('code')
                if s_code_value == '51001':
                    title = '模拟盘土狗币交易失败',
                    content = f'品种：{self.instId}不在交易所模拟盘中！'
                elif s_code_value == '50001':
                    title = '设置失败'
                    content = '交易所服务器异常，服务暂时不可用，请稍后重试！'
                elif s_code_value == '59102':
                    title = '交易失败'
                    content = '杠杆倍数超过最大杠杆倍数，请降低杠杆倍数！'
                elif s_code_value == '50105':
                    title =  'API错误'
                    content = 'PASSPHRASE填写错误，请结束任务，重新提交！'
                elif s_code_value == '50101':
                    title = 'API错误'
                    content = '添加的API并非模拟盘（或实盘）API，请重新提交对应环境的API！'
                elif s_code_value == '59000':
                    title = '设置失败'
                    content = '请在设置前关闭任何挂单或持仓！'
                elif s_code_value == '50110':
                    title = '交易失败'
                    content = '当前IP不在你的API白名单内，请前往交易所API管理页面添加IP白名单！'
                elif s_code_value == '50013':
                    title = '交易失败'
                    content = '交易所系统繁忙，导致交易失败。本次交易放弃。'
                else:
                    title = '交易失败'
                    content = f'请根据错误码(code)，自行在官网https://www.okx.com/docs-v5/zh/?python#error-code查看错误原因。错误信息：{result}'

                self.log_to_database("WARNING", title, content)
                Push(self.user_id, self.task_id, datetime.datetime.now(), self.instId, self.posSide, self.lever,
                     f'开仓失败(code:{s_code_value})', subject=title, body=content).push()
            except:
                pass

    # 手动结束跟单，打印日志
    def stop(self):
        try:
            self.acc, self.flag, self.ip_id = api(self.user_id, self.api_id)
            if int(self.fast_mode) == 1:
                res = self.check_ip()
                if res:
                    self.acc.pop("proxies")
            # 创建okx交易对象
            obj = app.OkxSWAP(**self.acc)
            self.obj = obj

            # 根据api选择实盘还是模拟盘
            obj.account.api.flag = self.flag
            obj.trade.api.flag = self.flag
            # 结束全部正在进行中的交易
            data = self.obj.account.get_positions().get('data')
            # 从交易所获取改为从数据库获取
            # with Connect() as db:
            #     data = db.fetch_all(
            #         "select * from api_orderinfo where user_id = %(user_id)s and task_id = %(task_id)s and status = 1",
            #         user_id=self.user_id, task_id=self.task_id)
        except Exception as e:
            print(f"{self.task_id}交易失败，原因: {e}")
            match = re.search(r'"code":"(\d+)"', str(e))
            if match:
                code_value = match.group(1)
                if code_value == '50101':
                    self.log_to_database("WARNING", "停止交易", "请确认APIKEY和实盘或者模拟盘环境匹配！")
                elif code_value == '50105':
                    self.log_to_database("WARNING", 'API错误', 'PASSPHRASE填写错误，请结束任务，重新提交！')
                elif code_value == '50001':
                    self.log_to_database("WARNING", '交易所服务错误', '交易所服务暂时不可用，请稍后重试！')
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
            if self.status == 2:
                self.log_to_database("WARNING", '手动结束跟单', f'任务：{self.task_id}')
            elif self.status == 3:
                self.log_to_database("WARNING", 'IP即将过期，提前被动结束跟单', f'任务：{self.task_id}')
            return

        market_data = []
        for item in data:
            market_data.append(
                dict(
                    instId=item.get('instId'),
                    posSide=item.get('posSide'),
                    mgnMode=item.get('mgnMode')
                )
            )
        if market_data:
            self.run_close_market_concurrently(market_data)
            # instId = item.get('instId')
            # posSide = item.get('posSide')
            # mgnMode = item.get('mgnMode')
            # # 市价平仓
            # try:
            #     self.obj.trade.close_market(instId=instId, posSide=posSide, quantityCT='all', tdMode=mgnMode)
            #     self.log_to_database("WARNING", '手动结束跟单', f'{instId}已经按市价进行平仓。')
            # except Exception as e:
            #     self.log_to_database("WARNING", '手动结束跟单', f'{instId}平仓失败，请手动平仓。')
            #     print(e)

        # 更新收益数据，以及对应可用额度数据。强制更新
        obj = OkxOrderInfo(self.user_id, self.task_id)
        while obj.get_order():
            obj.get_position_history(order_type=2)
        print(f'更新用户{self.user_id}任务{self.task_id}持仓数据成功！')

        # # 账户获取剩余额度
        # remaining_quota = get_remaining_quota(self.user_id, int(self.flag))
        # # 获取任务收益
        # task_pnl = check_task_pnl(self.task_id)
        # remaining_quota -= task_pnl
        # # 更新剩余额度数据
        # update_remaining_quota(self.user_id, int(self.flag), remaining_quota)
        #
        # print(f'更新用户{self.user_id}可用盈利额度数据成功！')
        if self.status == 2:
            self.log_to_database("WARNING", '手动结束跟单', f'任务：{self.task_id}')
        elif self.status == 3:
            self.log_to_database("WARNING", 'IP即将过期，提前被动结束跟单', f'任务：{self.task_id}')

    def close_pos(self, item):
        # 平仓
        instId = item.get('instId')
        posSide = item.get('posSide')
        mgnMode = item.get('mgnMode')
        quantityCT = item.get('quantityCT')
        if item.get('order_type') == 'close_all':
            try:
                clOrdId = uuid.uuid4().hex
                # res = self.obj.trade.close_market(instId=instId, posSide=posSide, quantityCT='all', tdMode=mgnMode)
                # autoCxl 自动撤单 撤销已存在得非市价平单
                res = self.obj.trade.set_close_position(instId=instId, posSide=posSide,mgnMode=mgnMode, autoCxl=True, clOrdId=clOrdId)
                if res.get("data")[0].get("clOrdId") == clOrdId:
                    print(f'##任务{self.task_id}全部平仓：品种:{instId}###{res}, 订单ID： {clOrdId}')
                else:
                    # TODO 返回值确认
                    # 平仓出错，拆分平仓
                    print(f'任务：{self.task_id}平仓出错，拆分平仓！')
                    market_data = self.close_market_2nd()
                    if market_data:
                        self.run_close_market_concurrently(market_data)
                title = "进行平仓操作"
                content = f"品种:{instId}，方向：{posSide}"
                self.log_to_database("success", title, content)
                Push(self.user_id, self.task_id, datetime.datetime.now(), self.instId, self.posSide, self.lever, 'close', subject=title, body=content).push()
            except Exception as e:
                title = "平仓操作失败"
                content = f"品种:{instId}，方向：{posSide}，平仓失败，请手动平仓。"
                self.log_to_database("WARNING", title, content)
                Push(self.user_id, self.task_id, datetime.datetime.now(), self.instId, self.posSide, self.lever, '平仓失败，请手动平仓', subject=title, body=content).push()
                print(e)
        elif item.get('order_type') == 'close_2nd':
            res = self.obj.trade.close_market(instId=instId, posSide=posSide, quantityCT=quantityCT, tdMode=mgnMode)
            print(f'##任务{self.task_id}分批平仓：品种:{instId}###{res}')
            if res.get('set_order_result', {}) is not None:
                title = "平仓操作失败"
                content = f"品种:{instId}，方向：{posSide}，平仓失败，请手动平仓。"
                self.log_to_database("WARNING", title, content)
                Push(self.user_id, self.task_id, datetime.datetime.now(), self.instId, self.posSide, self.lever, '平仓失败，请手动平仓', subject=title, body=content).push()
        else:
            try:
                # 假设self.obj是已经实例化的，可以执行trade.close_market的对象
                # res = self.obj.trade.close_market(instId=instId, posSide=posSide, quantityCT='all', tdMode=mgnMode)
                clOrdId = uuid.uuid4().hex
                res = self.obj.trade.set_close_position(instId=instId, posSide=posSide,mgnMode=mgnMode, autoCxl=True, clOrdId=clOrdId)
                if res.get("data")[0].get("clOrdId") == clOrdId:
                    print(f'##任务{self.task_id}全部平仓：品种:{instId}###{res}, 订单ID： {clOrdId}')
                else:
                    # TODO 返回值确认
                    # 平仓出错，拆分平仓
                    print(f'任务：{self.task_id}平仓出错，拆分平仓！')
                    market_data = self.close_market_2nd()
                    if market_data:
                        self.run_close_market_concurrently(market_data)
                print(f'##任务{self.task_id}全部平仓：品种:{instId}###{res}')
                self.log_to_database("WARNING", '手动结束跟单', f'{instId}已经按市价进行平仓。')
            except Exception as e:
                title = "手动结束跟单"
                content = f"品种:{instId}，方向：{posSide}，平仓失败，请手动平仓。"
                self.log_to_database("WARNING", title, content)
                Push(self.user_id, self.task_id, datetime.datetime.now(), self.instId, self.posSide, self.lever, '平仓失败，请手动平仓', subject=title, body=content).push()
                print(e)

    def run_close_market_concurrently(self, data):
        # 使用ThreadPoolExecutor创建线程池
        # max_workers参数可以根据需要调整，这里假定为10
        with ThreadPoolExecutor(max_workers=10) as executor:
            # 使用map方法并发执行close_pos方法
            # data是包含多个item的列表，每个item都会被传递给close_pos方法
            list(executor.map(self.close_pos, data))
        # threads = []
        # for item in data:
        #     # 为每个item创建一个线程
        #     thread = threading.Thread(target=self.close_pos, args=(item,))
        #     threads.append(thread)
        #     thread.start()
        #
        # # 等待所有线程完成
        # for thread in threads:
        #     thread.join()

    def update_task_with_ip(self):
        """
        更新任务表的ip_id
        """
        params = {
            "ip_id": self.ip_id,
            "task_id": self.task_id,
        }
        update_sql = """
            UPDATE api_taskinfo SET ip_id = %(ip_id)s WHERE id = %(task_id)s
        """
        with Connect() as db:
            db.exec(update_sql, **params)

    def write_task_log(self):
        """
        更新任务日志状态
        用于是否重新插入开始日志
        """
        with Connect() as db:
            res = db.fetch_one("select ip_id from api_taskinfo where id = %(task_id)s and status = 1",
                               task_id=self.task_id)
            if res.get("ip_id", None) is None:
                self.log_to_database("INFO", f"跟单猿交易系统启动", f"跟随交易员：{self.uniqueName}")

    def transform_sums(self):
        if self.order_type is None:
            return
        if self.order_type == 'change':
            self.margin = self.new_margin - self.old_margin
        if self.role_type == 1:
            self.sums = self.margin * self.ratio

    def check_ip(self):

        """
        更新任务表的ip_id
        """
        result = False
        with Connect() as db:
            res = db.fetch_one(
                "select ip from  api_apiinfo  WHERE api_key = %(api_key)s and secret_key = %(secret_key)s",
                api_key=self.acc.get("key"), secret_key=self.acc.get("secret"))
            if res.get("ip", None):
                arr = res["ip"].split(",")
                if HOST_IP in arr:
                    result = True
            else:
                result = True
        return result

    def close_market_2nd(self):
        import random
        def split_into_parts(total, parts=5):
            # 生成前 parts-1 个随机正整数
            random_parts = [random.randint(1, int(total - parts + 1)) for _ in range(parts - 1)]

            # 确保随机部分的和小于 total
            while sum(random_parts) >= total:
                random_parts = [random.randint(1, int(total - parts + 1)) for _ in range(parts - 1)]

            # 计算剩余部分，并确保其为正数
            remaining = total - sum(random_parts)
            if remaining <= 0:
                return split_into_parts(total, parts)

            split_parts = random_parts + [remaining]

            return split_parts

        data = self.obj.account.get_positions().get('data')
        if data == []:
            return
        for d in data:
            if d['instId'] == self.instId and \
                    d['mgnMode'] == self.mgnMode and \
                    d['posSide'] == self.posSide:
                availPos = float(d['availPos'])

        # 获取分好的部分
        split_parts = split_into_parts(availPos)
        # 将最后一个部分替换为 'all'
        split_parts[0] = 'all'
        market_data = []
        for i in split_parts:
            market_data.append(
                dict(
                    instId=self.instId,
                    posSide=self.posSide,
                    mgnMode=self.mgnMode,
                    order_type='close_2nd',
                    quantityCT=i
                )
            )

        return market_data
