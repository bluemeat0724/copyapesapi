import datetime
import threading
import time
import redis
from crawler import settingsdev as settings
import json
from loguru import logger
from crawler.spiders import okx_follow_spider
from crawler.spiders import okx_personal_spider
from crawler.utils.db import Connect

logger.remove()  # 移除所有默认的handler


class Spider(threading.Thread):
    def __init__(self, task_id, trader_platform, uniqueName, follow_type, role_type, reduce_ratio, sums, ratio,
                 lever_set, first_order_set, api_id,
                 user_id, leverage, posSide_set, fast_mode):
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

    def run(self):
        self.log_to_database("INFO", "跟单猿跟单系统启动", f"跟随交易员：{self.uniqueName}")
        # 第一次获取当前交易数据
        while True:
            try:
                old_list = self.summary()
                if old_list is None:
                    continue
                break
            except:
                self.log_to_database("error", "跟单猿跟单系统启动失败", "请检查代理IP是否还在有效期！")

        if old_list:
            self.log_to_database("INFO", f"交易员{self.uniqueName}有正在进行中的交易", "等待新的交易发生后开始跟随！")
            # self.log_to_database("debug", str(old_list))
        else:
            self.log_to_database("INFO", f"交易员{self.uniqueName}尚未开始交易", "等待新的交易发生后开始跟随！")

        while not self.stop_flag.is_set():
            new_list = self.summary()
            if new_list is None:
                continue
            res = self.analysis(old_list, new_list)
            if res is True:
                old_list = new_list
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
                summary_list_new = okx_personal_spider.spider(self.uniqueName)
                return summary_list_new
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
            elif item.get("follow_type") == 2:
                # 根据 order_type 调整 margin 值
                if item.get("order_type") != 'change':
                    item["margin"] = item["margin"] * float(item["lever"]) / self.leverage
                else:
                    item["old_margin"] = item["old_margin"] * float(item["lever"]) / self.leverage
                    item["new_margin"] = item["new_margin"] * float(item["lever"]) / self.leverage

                # 最后设置 lever
                item["lever"] = self.leverage
        return item

    # 数据分析脚本，连接交易脚本
    def analysis(self, old_list, new_list):
        if self.role_type == 1:
            self.analysis_okx_follow(old_list, new_list)
            return True
        elif self.role_type == 2:
            # # 将记录列表写入文本文件
            # with open(f'test_old_new_list_{self.uniqueName}.txt', 'a') as file:
            #     # 使用json.dumps将列表转换为字符串格式，便于阅读
            #     file.write(f'{datetime.datetime.now()}\n')
            #     file.write("old:\n")
            #     file.write(json.dumps(old_list, indent=4))
            #     file.write("new:\n")
            #     file.write(json.dumps(new_list, indent=4))
            res = self.analysis_okx_personal(old_list, new_list)
            if res is True:
                return True

    def analysis_okx_follow(self, old_list, new_list):
        # 如果没有交易数据，则直接返回
        if not new_list and not old_list:
            return None
        # 查找新增的交易数据
        name_set = set(i['instId'] for i in old_list)
        added_items = list(filter(lambda x: x['instId'] not in name_set, new_list))

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
                item = self.transform(item)
                # thread_logger.success(
                #     f"交易员{self.uniqueName}进行了开仓操作，品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}")
                self.log_to_database("success", f"交易员{self.uniqueName}进行了开仓操作",
                                     f"品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}")
                # 写入Redis队列
                conn = redis.Redis(**settings.REDIS_PARAMS)
                conn.lpush(settings.TRADE_TASK_NAME, json.dumps(item))
                time.sleep(0.5)

        # 查找减少的交易数据
        removed_items = [i for i in old_list if i['instId'] not in set(map(lambda x: x['instId'], new_list))]
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
                item = self.transform(item)
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
            if old_item["instId"] == new_item["instId"] and old_item['availSubPos'] != new_item['availSubPos']:
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
                          'fast_mode': self.fast_mode
                          }
                # thread_logger.success(
                #     f"交易员{self.uniqueName}进行了调仓操作，品种：{old_item['instId']}，原仓位保证金：{round(float(old_item['margin']),2)}USDT，现仓位保证金：{round(float(new_item['margin']),2)}USDT")
                self.log_to_database("success", f"交易员{self.uniqueName}进行了调仓操作",
                                     f"品种：{old_item['instId']}，原仓位保证金：{round(float(old_item['margin']), 2)}USDT，现仓位保证金：{round(float(new_item['margin']), 2)}USDT")
                change = self.transform(change)
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

        def complete_task_data(new, old):
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
                'fast_mode': self.fast_mode
            })
            if new['order_type'] == 'close' and old:
                # TODO 只能拿上一条记录的mgnMode，如果有全仓和逐仓同时出现的交易就有拿错的风险，避免风险只能去数据库里拿
                new['mgnMode'] = old.get('mgnMode', 'cross')
            # 重新设置杠杆
            item = self.transform(new)
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
                return None
            # new_list = okx_personal_spider.spider_close_item(self.uniqueName)
            # 如果old_list不为空，new_list为空，说明交易员已完全平仓，给交易脚本推送全部平仓命令
            complete_task_data({}, {})
            self.log_to_database("success", f"交易员{self.uniqueName}进行了平仓操作",
                                 "交易员当前没有任何持仓！")
            return True
            # if not new_list:
            #     print('return')
            #     self.log_to_database("WARNING", "网络错误", f"任务ID：{self.task_id}网络发生错误，交易员可能已经完全平仓。")
            #     return None

        if not old_list:
            if new_list[0]['order_type'] == 'open':
                openTime = transform_time(new_list[0]['openTime'])
                self.log_to_database("success", f"交易员{self.uniqueName}进行了开仓或加仓操作",
                                     f"品种：{new_list[0]['instId']}，杠杆：{new_list[0]['lever']}，方向：{new_list[0]['posSide']}，交易创建时间：{openTime}")
                complete_task_data(new_list[0], {})
        else:
            # 查找新增的交易数据
            time_set = set(i['openTime'] for i in old_list)
            added_items = list(filter(lambda x: x['openTime'] not in time_set, new_list))
            if added_items:
                for item in added_items:
                    action_map = {'open': "开仓或加仓", 'close': "平仓", 'reduce': "减仓"}
                    action = action_map.get(item['order_type'], "交易")
                    log_trade_action(action, item)
                    complete_task_data(item, old_list[0])
        return True
