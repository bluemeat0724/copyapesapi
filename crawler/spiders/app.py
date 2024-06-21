import datetime
import threading
import time
import redis
from crawler import settingsdev as settings
import json
from loguru import logger
from crawler.spiders import okx_follow_spider, okx_personal_spider_1
from crawler.spiders import okx_personal_spider
from crawler.spiders import okx_get_position
from crawler.utils.db import Connect

logger.remove()  # 移除所有默认的handler


class Spider(threading.Thread):
    def __init__(self, task_id, trader_platform, uniqueName, follow_type, role_type, reduce_ratio, sums, ratio,
                 lever_set, first_order_set, api_id,
                 user_id, leverage, posSide_set, fast_mode, investment, trade_trigger_mode, sl_trigger_px, tp_trigger_px, first_open_type, uplRatio):
        super(Spider, self).__init__()
        self.task_id = task_id
        self.trader_platform = trader_platform
        self.uniqueName = uniqueName
        self.follow_type = follow_type
        self.role_type = role_type
        self.reduce_ratio = reduce_ratio
        self.sums = sums
        self.ratio = ratio
        self.lever_set = lever_set
        self.first_order_set = first_order_set
        self.api_id = api_id
        self.user_id = user_id
        self.leverage = leverage
        self.posSide_set = posSide_set
        self.stop_flag = threading.Event()  # 用于控制爬虫线程的停止
        self.status = None  # status 1:开始 2：手动结束 3：ip到期 被动结束
        self.fast_mode = fast_mode  # 0:否 1:是
        self.investment = investment
        self.trade_trigger_mode = trade_trigger_mode
        self.sl_trigger_px = sl_trigger_px
        self.tp_trigger_px = tp_trigger_px
        self.first_open_type = first_open_type
        self.uplRatio = uplRatio
        self.old_position = []
        self.new_position = []
        self.my_position = [] # {'instId': '', 'mgnMode': '','posSide': '', 'margin': ''}记录当前自己的仓位价值，计算需要加减仓量

    def log_to_database(self, level, title, description=""):
        """
        手动保存日志信息到数据库
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
                        INSERT INTO api_spiderlog (user_id, task_id, date, color, title, description, created_at, updated_at)
                        VALUES (%(user_id)s, %(task_id)s, %(date)s, %(color)s, %(title)s, %(description)s, NOW(), NOW())
                    """
        with Connect() as db:
            db.exec(insert_sql, **params)

    def write_task_log(self, log_type):
        """
        更新任务日志状态
        用于是否重新插入开始日志
        """
        with Connect() as db:
            res = db.fetch_one("select ip_id from api_taskinfo where id = %(task_id)s and status = 1", task_id=self.task_id)
            if res.get("ip_id", None) is None:
                if log_type == 1:
                    self.log_to_database("INFO", f"跟单猿交易系统启动", f"跟随交易员：{self.uniqueName}")
                elif log_type == 2:
                    self.log_to_database("INFO", f"交易员{self.uniqueName}有正在进行中的交易", "等待新的交易发生后开始跟随！")
                elif log_type == 3:
                    self.log_to_database("INFO", f"交易员{self.uniqueName}尚未开始交易", "等待新的交易发生后开始跟随！")

    def run(self):
        self.write_task_log(1)
        # self.log_to_database("INFO", "跟单猿跟单系统启动", f"跟随交易员：{self.uniqueName}")
        # 第一次获取当前交易数据
        while True:
            try:
                old_list = self.summary()
                self.old_position = self.new_position
                if old_list is None:
                    continue
                break
            except:
                self.log_to_database("error", "跟单猿跟单系统启动失败", "请检查代理IP是否还在有效期！")

        if old_list:
            self.write_task_log(2)
            # self.log_to_database("INFO", f"交易员{self.uniqueName}有正在进行中的交易", "等待新的交易发生后开始跟随！")
        else:
            self.write_task_log(3)
            # self.log_to_database("INFO", f"交易员{self.uniqueName}尚未开始交易", "等待新的交易发生后开始跟随！")

        while not self.stop_flag.is_set():
            new_list = self.summary()
            if new_list is None:
                continue
            self.analysis(old_list, new_list)
            old_list = new_list
            # if self.trader_platform == 1 and self.role_type == 2:
            #     self.old_position = self.new_position
            # if self.trader_platform == 1 and self.role_type == 1:
            time.sleep(1)

    def stop(self):
        # 设置停止标志，用于停止爬虫线程
        self.stop_flag.set()
        if self.status == 2:
            self.log_to_database("WARNING", "手动结束跟单", f"任务ID：{self.task_id}")
        elif self.status == 3:
            self.log_to_database("WARNING", "IP即将到期提前结束跟单", f"任务ID：{self.task_id}")

    # 解耦爬虫脚本，获取交易数据
    def summary(self):
        if self.role_type == 1:
            if self.trader_platform == 1:
                summary_list_new = okx_follow_spider.spider(self.uniqueName, self.follow_type, self.task_id,
                                                            self.trader_platform, self.sums, self.ratio, self.lever_set,
                                                            self.first_order_set, self.api_id, self.user_id)
                return summary_list_new
            else:
                return None
        elif self.role_type == 2:
            if self.trader_platform == 1:
                # result = okx_personal_spider.spider(self.uniqueName)
                # if result is not None:
                #     summary_list_new, self.new_position = result
                #     return summary_list_new
                # else:
                #     return None
                result = okx_personal_spider_1.spider(self.uniqueName)
                if result is not None:
                    return result
                else:
                    return None
            else:
                return None

    def transform(self, item):
        item['posSide_set'] = self.posSide_set
        # 当 lever_set == 2 时，根据 follow_type 的不同情况处理
        if item.get("lever_set") == 2:
            # 如果 follow_type == 1，简单地设置 lever
            if item.get("follow_type") == 1:
                item["lever"] = self.leverage

            # 如果 follow_type == 2，进一步处理
            elif item.get("follow_type") == 2:  # 跟单ok普通用户不支持自定义杠杆（无意义）
                # 根据 order_type 调整 margin 值
                if item.get("order_type") != 'change':
                    item["margin"] = item["margin"] * float(item["lever"]) / self.leverage
                else:
                    item["old_margin"] = item["old_margin"] * float(item["lever"]) / self.leverage
                    item["new_margin"] = item["new_margin"] * float(item["lever"]) / self.leverage
                # 最后设置 lever
                item["lever"] = self.leverage
        else:
            # 如果没有自定义杠杆，且是按比例跟单，计算出跟单普通交易员的交易金额
            if self.role_type == 2 and item.get("follow_type") == 2:
                if item.get("order_type") in ['close', 'close_all']:
                    return item
                # 通过api_id查当前usdt资产
                with Connect() as conn:
                    usdt = conn.fetch_one(
                        "select usdt from api_apiinfo where id=%(id)s AND deleted=0",
                        id={self.api_id}).get('usdt')
                notionalUsd = self.is_in_my_position(item)
                if notionalUsd:
                    if item.get("order_type") =='open':
                        if float(usdt) > self.investment:
                            print(f"【2-开加仓-1】任务id:{self.task_id}，总投资：{self.investment}，{item['instId']}仓位：{item['posSpace']}")
                            # new_notionalUsd = float(usdt.get("usdt", 0)) * item['posSpace'] / float(item['lever'])
                            new_notionalUsd = self.investment * item['posSpace']
                        else:
                            print(f"【2-开加仓-2】任务id:{self.task_id}，总投资：{usdt}，{item['instId']}仓位：{item['posSpace']}")
                            new_notionalUsd = float(usdt) * item['posSpace']
                        print(f'notionalUsd:{notionalUsd}, new_notionalUsd:{new_notionalUsd}')
                        item['sums'] = (float(new_notionalUsd) - float(notionalUsd)) / float(item['lever'])
                        # 如果计算的开仓金额小于0，说明当前仓位比例过高，则不进行开仓
                        if item['sums'] < 0:
                            item['sums'] = 0
                        print(f'【2-开加仓】任务id:{self.task_id}，开单金额：{item["sums"]}')
                    elif item.get("order_type") == 'reduce':
                        if float(usdt) > self.investment:
                            print(f"【2-减仓-1】任务id:{self.task_id}，总投资：{self.investment}，{item['instId']}仓位：{item['posSpace']}")
                            new_notionalUsd = self.investment * item['posSpace']
                        else:
                            print(f"【2-减仓-2】任务id:{self.task_id}，总投资：{usdt}，{item['instId']}仓位：{item['posSpace']}")
                            new_notionalUsd = float(usdt) * item['posSpace']
                        print(f'notionalUsd:{notionalUsd}, new_notionalUsd:{new_notionalUsd}')
                        item['sums'] = (float(notionalUsd) - float(new_notionalUsd)) / float(item['lever'])
                        # if item['sums'] < 0:
                        #     item['sums'] = 0
                        print(f'【2-减仓】任务id:{self.task_id}，减仓金额：{item["sums"]}')
                else:
                    if item.get("order_type") == 'open':
                        if float(usdt) > self.investment:
                            print(f"【2-开加仓-1】任务id:{self.task_id}，总投资：{self.investment}，{item['instId']}仓位：{item['posSpace']}")
                            item['sums'] = self.investment * item['posSpace'] / float(item['lever'])
                        else:
                            print(f"【2-开加仓-2】任务id:{self.task_id}，总投资：{usdt}，{item['instId']}仓位：{item['posSpace']}")
                            item['sums'] = float(usdt) * item['posSpace'] / float(item['lever'])
                        print(f'【2-开加仓】任务id:{self.task_id}，开单金额：{item["sums"]}')
                    else:
                        item['sums'] = 0
        return item

    def is_in_my_position(self,new_dict):
        self.my_position = okx_get_position.get_position(self.user_id, self.task_id)
        for d in self.my_position:
            if d['instId'] == new_dict['instId'] and \
                    d['mgnMode'] == new_dict['mgnMode'] and \
                    d['posSide'] == new_dict['posSide']:
                return d['notionalUsd']
        return False

    # 数据分析脚本，连接交易脚本
    def analysis(self, old_list, new_list):
        if self.role_type == 1:
            self.analysis_okx_follow(old_list, new_list)
            return True
        elif self.role_type == 2:
            # self.analysis_okx_personal(old_list, new_list)
            self.analysis_okx_personal_1(old_list, new_list)

    def analysis_okx_follow(self, old_list, new_list):
        # 如果没有交易数据，则直接返回
        if not new_list and not old_list:
            return None
        # 查找新增的交易数据
        # 将旧列表中的(instId, mgnMode)对存入集合
        old_set = set(i for i in old_list)
        # 使用(instId, mgnMode)对来判断新列表中的新增项
        added_items = list(filter(lambda x: x not in old_set, new_list))
        redis_server = RedisHandler(settings.REDIS_PARAMS)
        # 获取redis 队列中的数据
        # 判断待跟单的交易是否满足开仓要求
        for item in new_list:
            if redis_server.hget_task(self.task_id, item):
                item['order_type'] = 'open'
                item['task_id'] = self.task_id
                item['trader_platform'] = self.trader_platform
                item['follow_type'] = self.follow_type
                item['uniqueName'] = self.uniqueName
                item['role_type'] = self.role_type
                item['reduce_ratio'] = self.reduce_ratio
                item['sums'] = self.sums
                item['ratio'] = self.ratio
                item['lever_set'] = self.lever_set
                item['first_order_set'] = self.first_order_set
                item['api_id'] = self.api_id
                item['user_id'] = self.user_id
                item['fast_mode'] = self.fast_mode
                item['investment'] = self.investment
                item['trade_trigger_mode'] = self.trade_trigger_mode
                item['sl_trigger_px'] = self.sl_trigger_px
                item['tp_trigger_px'] = self.tp_trigger_px
                item = self.transform(item)
                # 判断是否符合要求, 如何符合则开单，不符合则跳过
                res = self.check_open_type_and_upl_ratio(self.first_open_type, self.uplRatio, item['upl_ratio'])
                if res:
                    # 写入Redis队列
                    self.log_to_database("success", f"交易员{self.uniqueName}进行了开仓操作",
                                         f"品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}, 当前交易员的盈利率为：{item['upl_ratio']}, 符合开仓条件")
                    # 删除redis task item
                    redis_server.hdel_task(self.task_id, item)
                    item.pop('upl_ratio', None)
                    item.pop('side', None)
                    conn = redis.Redis(**settings.REDIS_PARAMS)
                    conn.lpush(settings.TRADE_TASK_NAME, json.dumps(item))
                    time.sleep(0.5)
                else:
                    task_instId = redis_server.hget_task(self.task_id, item)
                    if not task_instId:
                        # 存入redis
                        redis_server.hset_task(self.task_id, item)
                        self.log_to_database("success", f"交易员{self.uniqueName}进行了开仓操作",
                                             f"品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}, 当前交易员的盈利率为：{item['upl_ratio']}，不符合开仓条件")

        if added_items:
            for item in added_items:
                item['order_type'] = 'open'
                item['task_id'] = self.task_id
                item['trader_platform'] = self.trader_platform
                item['follow_type'] = self.follow_type
                item['uniqueName'] = self.uniqueName
                item['role_type'] = self.role_type
                item['reduce_ratio'] = self.reduce_ratio
                item['sums'] = self.sums
                item['ratio'] = self.ratio
                item['lever_set'] = self.lever_set
                item['first_order_set'] = self.first_order_set
                item['api_id'] = self.api_id
                item['user_id'] = self.user_id
                item['fast_mode'] = self.fast_mode
                item['investment'] = self.investment
                item['trade_trigger_mode'] = self.trade_trigger_mode
                item['sl_trigger_px'] = self.sl_trigger_px
                item['tp_trigger_px'] = self.tp_trigger_px
                item = self.transform(item)
                # 判断是否符合要求, 如何符合则开单，不符合则跳过
                res = self.check_open_type_and_upl_ratio(self.first_open_type, self.uplRatio, item['upl_ratio'])
                if res:
                    # 写入Redis队列
                    self.log_to_database("success", f"交易员{self.uniqueName}进行了开仓操作",
                                         f"品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}, 当前交易员的盈利率为：{item['upl_ratio']}, 符合开仓条件")
                    # 删除redis task item
                    redis_server.hdel_task(self.task_id, item)
                    item.pop('upl_ratio', None)
                    item.pop('side', None)
                    conn = redis.Redis(**settings.REDIS_PARAMS)
                    conn.lpush(settings.TRADE_TASK_NAME, json.dumps(item))
                    time.sleep(0.5)
                else:
                    task_instId = redis_server.hget_task(self.task_id, item)
                    if not task_instId:
                        # 存入redis
                        redis_server.hset_task(self.task_id, item)
                        self.log_to_database("success", f"交易员{self.uniqueName}进行了开仓操作",
                                             f"品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}, 当前交易员的盈利率为：{item['upl_ratio']}，不符合开仓条件")


        # 查找减少的交易数据
        removed_items = [i for i in old_list if (i['instId'], i['mgnMode'])not in set(map(lambda x: (x['instId'], x['mgnMode']), new_list))]
        # logger.debug('removed_items:',removed_items)
        if removed_items:      
            for item in removed_items:
                item['order_type'] = 'close'
                item['task_id'] = self.task_id
                item['trader_platform'] = self.trader_platform
                item['follow_type'] = self.follow_type
                item['uniqueName'] = self.uniqueName
                item['role_type'] = self.role_type
                item['reduce_ratio'] = self.reduce_ratio
                item['sums'] = self.sums
                item['ratio'] = self.ratio
                item['lever_set'] = self.lever_set
                item['first_order_set'] = self.first_order_set
                item['api_id'] = self.api_id
                item['user_id'] = self.user_id
                item['fast_mode'] = self.fast_mode
                item['investment'] = self.investment
                item['trade_trigger_mode'] = self.trade_trigger_mode
                item['sl_trigger_px'] = self.sl_trigger_px
                item['tp_trigger_px'] = self.tp_trigger_px
                item = self.transform(item)
                # thread_logger.success(
                #     f"交易员{self.uniqueName}进行了平仓操作，品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}")
                self.log_to_database("success", f"交易员{self.uniqueName}进行了平仓操作",
                                    f"品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}")

                # 删除redis
                redis_server.hdel_task(self.task_id, item)
                # 写入Redis队列
                item.pop('upl_ratio', None)
                item.pop('side', None)
                conn = redis.Redis(**settings.REDIS_PARAMS)
                conn.lpush(settings.TRADE_TASK_NAME, json.dumps(item))
                time.sleep(0.5)

            # if task_instId:
            #     continue 
            # 查找值变化的数据
        changed_items = []
        for old_item, new_item in zip(old_list, new_list):
            if old_item["instId"] == new_item["instId"] and old_item["mgnMode"] == new_item["mgnMode"] and old_item['availSubPos'] != new_item['availSubPos']:
                change = {'order_type': 'change',
                        'instId': old_item['instId'],
                        'old_availSubPos': old_item['availSubPos'],
                        'new_availSubPos': new_item['availSubPos'],
                        'old_margin': float(old_item['margin']),
                        'new_margin': float(new_item['margin']),
                        'mgnMode': old_item['mgnMode'],
                        'posSide': old_item['posSide'],
                        'lever': old_item['lever'],
                        'task_id': self.task_id,
                        'trader_platform': self.trader_platform,
                        'follow_type': self.follow_type,
                        'uniqueName': self.uniqueName,
                        'role_type': self.role_type,
                        'reduce_ratio': self.reduce_ratio,
                        'sums': self.sums,
                        'ratio': self.ratio,
                        'lever_set': self.lever_set,
                        'first_order_set': self.first_order_set,
                        'api_id': self.api_id,
                        'user_id': self.user_id,
                        'fast_mode': self.fast_mode,
                        'investment': self.investment,
                        'trade_trigger_mode': self.trade_trigger_mode,
                        'sl_trigger_px': self.sl_trigger_px,
                        'tp_trigger_px': self.tp_trigger_px
                        }
                # thread_logger.success(
                #     f"交易员{self.uniqueName}进行了调仓操作，品种：{old_item['instId']}，原仓位保证金：{round(float(old_item['margin']),2)}USDT，现仓位保证金：{round(float(new_item['margin']),2)}USDT")
                change = self.transform(change)
                changed_items.append(change)
                # 判断是否符合要求, 如何符合则开单，不符合则跳过
                if redis_server.hget_task(self.task_id, item):
                    self.log_to_database("success", f"交易员{self.uniqueName}进行了调仓操作",
                                         f"品种：{old_item['instId']}，尚未达到开仓条件，不进行加仓！")
                else:
                    self.log_to_database("success", f"交易员{self.uniqueName}进行了调仓操作",
                                         f"品种：{old_item['instId']}，原仓位保证金：{round(float(old_item['margin']), 2)}USDT，现仓位保证金：{round(float(new_item['margin']), 2)}USDT")
                    # 写入Redis队列
                    item.pop('upl_ratio', None)
                    item.pop('side', None)
                    conn = redis.Redis(**settings.REDIS_PARAMS)
                    conn.lpush(settings.TRADE_TASK_NAME, json.dumps(change))
                    print(change)
                    time.sleep(0.5)
        # 写入Redis队列

    def analysis_okx_personal_1(self, old_list, new_list):
        # 查找新增的交易数据
        old_set = set((i['instId'], i['mgnMode']) for i in old_list)
        # 使用(instId, mgnMode)对来判断新列表中的新增项
        added_items = list(filter(lambda x: (x['instId'], x['mgnMode']) not in old_set, new_list))

        if added_items:
            for item in added_items:
                item['order_type'] = 'open'
                item['task_id'] = self.task_id
                item['trader_platform'] = self.trader_platform
                item['follow_type'] = self.follow_type
                item['uniqueName'] = self.uniqueName
                item['role_type'] = self.role_type
                item['reduce_ratio'] = self.reduce_ratio
                item['sums'] = self.sums
                item['ratio'] = self.ratio
                item['lever_set'] = self.lever_set
                item['first_order_set'] = self.first_order_set
                item['api_id'] = self.api_id
                item['user_id'] = self.user_id
                item['fast_mode'] = self.fast_mode
                item['investment'] = self.investment
                item['trade_trigger_mode'] = self.trade_trigger_mode
                item['sl_trigger_px'] = self.sl_trigger_px
                item['tp_trigger_px'] = self.tp_trigger_px
                item = self.transform(item)
                item.pop('posSpace')
                item.pop('pos')
                item.pop('upl_ratio', None)
                # thread_logger.success(
                #     f"交易员{self.uniqueName}进行了开仓操作，品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}")
                self.log_to_database("success", f"交易员{self.uniqueName}进行了开仓操作",
                                     f"品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}")
                # 写入Redis队列
                conn = redis.Redis(**settings.REDIS_PARAMS)
                conn.lpush(settings.TRADE_TASK_NAME, json.dumps(item))
                time.sleep(0.5)

        # 查找减少的交易数据
        removed_items = [i for i in old_list if (i['instId'], i['mgnMode'])not in set(map(lambda x: (x['instId'], x['mgnMode']), new_list))]
        # logger.debug('removed_items:',removed_items)
        if removed_items:
            for item in removed_items:
                item['order_type'] = 'close'
                item['task_id'] = self.task_id
                item['trader_platform'] = self.trader_platform
                item['follow_type'] = self.follow_type
                item['uniqueName'] = self.uniqueName
                item['role_type'] = self.role_type
                item['reduce_ratio'] = self.reduce_ratio
                item['sums'] = self.sums
                item['ratio'] = self.ratio
                item['lever_set'] = self.lever_set
                item['first_order_set'] = self.first_order_set
                item['api_id'] = self.api_id
                item['user_id'] = self.user_id
                item['fast_mode'] = self.fast_mode
                item['investment'] = self.investment
                item['trade_trigger_mode'] = self.trade_trigger_mode
                item['sl_trigger_px'] = self.sl_trigger_px
                item['tp_trigger_px'] = self.tp_trigger_px
                item = self.transform(item)

                item.pop('posSpace')
                item.pop('pos')
                item.pop('upl_ratio', None)
                # thread_logger.success(
                #     f"交易员{self.uniqueName}进行了平仓操作，品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}")
                self.log_to_database("success", f"交易员{self.uniqueName}进行了平仓操作",
                                     f"品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}")
                # 写入Redis队列
                conn = redis.Redis(**settings.REDIS_PARAMS)
                conn.lpush(settings.TRADE_TASK_NAME, json.dumps(item))
                time.sleep(0.5)

        # 查找值变化的数据
        changed_items = []
        for old_item, new_item in zip(old_list, new_list):
            # 检查instId, mgnMode, posSide是否相同，并且availSubPos字段不存在于原始代码中，因此忽略这个条件
            if old_item["instId"] == new_item["instId"] and old_item["mgnMode"] == new_item["mgnMode"] and old_item[
                "posSide"] == new_item["posSide"]:
                old_posSpace = old_item.get('posSpace', 0)
                new_posSpace = new_item.get('posSpace', 0)
                # 计算posSpace的变动比例

                if old_posSpace != 0:
                    change_percentage = (new_posSpace - old_posSpace) / old_posSpace
                else:
                    change_percentage = 0

                # 检查变动是否超过10%
                if abs(change_percentage) > 0.02:
                    print("原始仓位old-new-差值", old_posSpace, new_posSpace, change_percentage, old_item['lever'])
                    order_type = 'open' if change_percentage > 0 else 'reduce'
                    change = {
                        'order_type': order_type,
                        'instId': old_item['instId'],
                        'mgnMode': old_item['mgnMode'],
                        'posSide': old_item['posSide'],
                        'lever': old_item['lever'],
                        'task_id': self.task_id,
                        'trader_platform': self.trader_platform,
                        'follow_type': self.follow_type,
                        'uniqueName': self.uniqueName,
                        'role_type': self.role_type,
                        'reduce_ratio': self.reduce_ratio,
                        'sums': self.sums,
                        'ratio': self.ratio,
                        'lever_set': self.lever_set,
                        'first_order_set': self.first_order_set,
                        'api_id': self.api_id,
                        'user_id': self.user_id,
                        'fast_mode': self.fast_mode,
                        'investment': self.investment,
                        'trade_trigger_mode': self.trade_trigger_mode,
                        'sl_trigger_px': self.sl_trigger_px,
                        'tp_trigger_px': self.tp_trigger_px,
                        'posSpace': new_posSpace,
                    }
                    self.log_to_database("success", f"交易员{self.uniqueName}进行了调仓操作",
                                     f"品种：{old_item['instId']}，原仓位：{round(old_posSpace * 100, 2)}%，现仓位：{round(new_posSpace * 100, 2)}%")
                    change = self.transform(change)
                    change.pop('posSpace')
                    change.pop('upl_ratio', None)
                    changed_items.append(change)

                    # 写入Redis队列
                    conn = redis.Redis(**settings.REDIS_PARAMS)
                    conn.lpush(settings.TRADE_TASK_NAME, json.dumps(change))
                    time.sleep(0.5)

    def analysis_okx_personal(self, old_list, new_list):
        def log_trade_action(action, item):
            """ 用于记录交易行为到数据库的辅助函数 """
            openTime = transform_time(item['openTime'])
            self.log_to_database("success", f"交易员{self.uniqueName}进行了{action}操作",
                                 f"品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}，交易创建时间：{openTime}")

        def complete_task_data(new):
            """补全任务数据并发送redis"""
            # new_list为空，说明交易员已完全平仓
            if not new:
                new = {
                    'order_type': 'close_all'
                }
            new.update({
                'task_id': self.task_id,
                'trader_platform': self.trader_platform,
                'follow_type': self.follow_type,
                'uniqueName': self.uniqueName,
                'role_type': self.role_type,
                'reduce_ratio': self.reduce_ratio,
                'sums': self.sums,
                'ratio': self.ratio,
                'lever_set': self.lever_set,
                'first_order_set': self.first_order_set,
                'api_id': self.api_id,
                'user_id': self.user_id,
                'fast_mode': self.fast_mode,
                'investment': self.investment,
                'trade_trigger_mode': self.trade_trigger_mode,
                'sl_trigger_px': self.sl_trigger_px,
                'tp_trigger_px': self.tp_trigger_px
            })
            # if new['order_type'] == 'close' and old:
            #     # TODO 只能拿上一条记录的mgnMode，如果有全仓和逐仓同时出现的交易就有拿错的风险，避免风险只能去数据库里拿
            #     new['mgnMode'] = old.get('mgnMode', 'cross')
            # 重新设置杠杆
            item = self.transform(new)
            if item['order_type'] != 'close' and item['order_type'] != 'close_all':
                item.pop('posSpace')
            # 写入Redis队列
            conn = redis.Redis(**settings.REDIS_PARAMS)
            conn.lpush(settings.TRADE_TASK_NAME, json.dumps(item))
            time.sleep(0.5)

        def transform_time(openTime):
            timestamp_seconds = int(openTime) / 1000
            dt_utc = datetime.datetime.utcfromtimestamp(timestamp_seconds)
            timezone_offset = datetime.timedelta(hours=8)
            dt_east_asian = dt_utc + timezone_offset
            formatted_datetime = dt_east_asian.strftime('%Y-%m-%d %H:%M:%S')
            return formatted_datetime

        if not new_list:
            if not old_list:
                return
            # new_list = okx_personal_spider.spider_close_item(self.uniqueName)
            # 如果old_list不为空，new_list为空，说明交易员已完全平仓，给交易脚本推送全部平仓命令
            complete_task_data({})
            self.log_to_database("success", f"交易员{self.uniqueName}进行了平仓操作",
                                 "交易员当前没有任何持仓！")
            print(f'{self.task_id}new_position:', self.new_position)
            return

        if not old_list:
            if new_list[0]['order_type'] == 'open':
                openTime = transform_time(new_list[0]['openTime'])
                self.log_to_database("success", f"交易员{self.uniqueName}进行了开仓或加仓操作",
                                     f"品种：{new_list[0]['instId']}，杠杆：{new_list[0]['lever']}，方向：{new_list[0]['posSide']}，交易创建时间：{openTime}")
                if self.follow_type == 2:
                    for position in self.new_position:
                        if new_list[0]['instId'] == position.get('instId') and new_list[0]['mgnMode'] == position.get('mgnMode'):
                            new_list[0]['posSpace'] = float(position.get('posSpace'))
                            print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}【1-开仓】任务id:{self.task_id}，开仓：{new_list[0]['posSpace']}")
                self.old_position = self.new_position
                complete_task_data(new_list[0])
                print(f'{self.task_id}new_position:', self.new_position)
        else:
            # 查找新增的交易数据
            time_set = set(i['openTime'] for i in old_list)
            added_items = list(filter(lambda x: x['openTime'] not in time_set, new_list))
            if added_items:
                for item in added_items:
                    action_map = {'open': "开仓或加仓", 'close': "平仓", 'reduce': "减仓"}
                    action = action_map.get(item['order_type'], "交易")
                    log_trade_action(action, item)

                    if self.follow_type == 2:
                        if item['order_type'] == 'open':
                            for position in self.new_position:
                                if position.get('instId') == item['instId'] and position.get('mgnMode') == item['mgnMode']:
                                    item['posSpace'] = float(position.get('posSpace'))
                                    print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}【1-加仓】任务id:{self.task_id}，仓位：{item['posSpace']}")

                        elif item['order_type'] == 'reduce':
                            for position in self.new_position:
                                if position.get('instId') == item['instId'] and position.get('mgnMode') == item['mgnMode']:
                                    item['posSpace'] = float(position.get('posSpace'))
                                    print(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}【1-减仓】任务id:{self.task_id}，仓位：{item["posSpace"]}')

                    print(f'{self.task_id}new_position:', self.new_position)
                    print(f'{self.task_id}old_position:', self.old_position)

                    if item['order_type'] == 'close':
                        print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}【1-平仓】任务id:{self.task_id}")
                        print(f'{item}')
                        removed_items = [i for i in self.old_position if (i['instId'], i['mgnMode']) not in set(
                            map(lambda x: (x['instId'], x['mgnMode']), self.new_position))]
                        for position in removed_items:
                            if position['instId'] == item['instId']:
                                item['mgnMode'] = position['mgnMode']
                                self.old_position.remove(position)
                                print(f"【{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}1-平仓】任务id:{self.task_id}，平仓：{item['instId']}，{item['mgnMode']}")
                    complete_task_data(item)
                self.old_position = self.new_position

    def check_open_type_and_upl_ratio(self,first_open_type, uplRatio, upl_ratio):
        """
        检查开仓模式和用户收益率，并根据条件返回结果。

        参数:
        first_open_type (int): 开仓模式，1表示当前市价，2表示区间限价。
        uplRatio (float): 用户收益率。
        upl_ratio (float): 交易员当前收益率。
        
        返回:
        bool: 如果满足条件返回True，否则返回False。
        """
        # 将交易员当前收益率除以100
        uplRatio /= 100

        # 判断开仓模式
        if first_open_type == 1:
            return True
        elif first_open_type == 2:
            # 判断用户收益率是否小于交易员当前收益率
            if float(upl_ratio) < float(uplRatio):
                return True
            else:
                return False
        else:
            # 如果开仓模式不是1或2，返回False
            return False
        


class RedisHandler:
    def __init__(self, redis_params):
        self.conn = redis.Redis(**redis_params)

    def hset_task(self, task_id, item):
        """
        设置 Redis 哈希表中的值。

        参数:
        task_id (str): 任务ID。
        item (dict): 包含 instId, mgnMode, posSide, side 的字典。
        """
        key = f"{task_id}_{item['instId']}_{item['mgnMode']}_{item['posSide']}_{item['side']}"
        value = 1
        self.conn.hset(task_id, key, value)

    def hget_task(self, task_id, item):
        """
        查询 Redis 哈希表中的值。

        参数:
        task_id (str): 任务ID。
        item (dict): 包含 instId, mgnMode, posSide, side 的字典。

        返回:
        str: 查询到的值，如果不存在则返回 None。
        """
        key = f"{task_id}_{item['instId']}_{item['mgnMode']}_{item['posSide']}_{item['side']}"
        return self.conn.hget(task_id, key)

    def hdel_task(self, task_id, item):
        """
        删除 Redis 哈希表中的值。

        参数:
        task_id (str): 任务ID。
        item (dict): 包含 instId, mgnMode, posSide, side 的字典。
        """
        key = f"{task_id}_{item['instId']}_{item['mgnMode']}_{item['posSide']}_{item['side']}"
        self.conn.hdel(task_id, key)

    def delete_task(self, task_id):
        """
        删除 Redis 中指定 task_id 的整个哈希表。

        参数:
        task_id (str): 任务ID。
        """
        self.conn.delete(task_id)
