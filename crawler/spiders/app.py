import datetime
import threading
import time
import redis
from crawler import settingsdev as settings
import json
from loguru import logger
from crawler.spiders import okx_follow_spider
from crawler.utils.db import Connect

logger.remove()  # 移除所有默认的handler



class Spider(threading.Thread):
    def __init__(self, task_id, trader_platform, uniqueName, follow_type, sums, lever_set, first_order_set, api_id,
                 user_id, ):
        super(Spider, self).__init__()
        self.task_id = task_id
        self.trader_platform = trader_platform
        self.uniqueName = uniqueName
        self.follow_type = follow_type
        self.sums = sums
        self.lever_set = lever_set
        self.first_order_set = first_order_set
        self.api_id = api_id
        self.user_id = user_id
        self.stop_flag = threading.Event()  # 用于控制爬虫线程的停止
        # self.thread_logger = None

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
        # self.setup_logger()
        # thread_logger = logger.bind(user_id=self.user_id, task_id=self.task_id)
        # self.thread_logger = thread_logger
        # thread_logger.info(f"跟单猿跟单系统启动，跟随交易员：{self.uniqueName}")
        self.log_to_database("info", f"跟单猿跟单系统启动，跟随交易员：{self.uniqueName}")
        # 第一次获取当前交易数据
        while True:
            try:
                old_list = self.summary()
                if old_list == None:
                    continue
                break
            except:
                self.log_to_database("error", "跟单猿跟单系统启动失败", "请检查API是否添加正确，代理IP是否还在有效期！")

        if old_list:
            self.log_to_database("INFO", f"交易员{self.uniqueName}有正在进行中的交易", "等待新的交易发生后开始跟随！")
            # self.log_to_database("debug", str(old_list))
        else:
            self.log_to_database("INFO", f"交易员{self.uniqueName}尚未开始交易", "等待新的交易发生后开始跟随！")

        # 断线次数
        count = 0
        max_count = 1
        # 是否打印日志的标记
        log_print = True
        # 网络超时判断
        timeout = False

        while not self.stop_flag.is_set():
            try:
                new_list = self.summary()
                if new_list == None:
                    continue
                # 网络恢复
                if timeout:
                    timeout = False
                    print(f"任务{self.task_id}网络恢复")
                    count = 0  # 重置计数器
                    log_print = True  # 重置日志打印标记
            except:
                timeout = True
                count += 1
                if count <= max_count and log_print:
                    print(f"任务{self.task_id}网络中断，正在尝试重新连接网络...")
                elif count > max_count and log_print:
                    log_print = False  # 超过{max_count}次后停止打印日志

                time.sleep(10)
                continue

            self.analysis(old_list, new_list)
            old_list = new_list
            time.sleep(1)

    def stop(self):
        # 设置停止标志，用于停止爬虫线程
        self.stop_flag.set()
        # self.thread_logger.WARNING(f"手动结束跟单，任务ID：{self.task_id}")
        self.log_to_database("WARNING", "手动结束跟单", f"任务ID：{self.task_id}")

    # 解耦爬虫脚本，获取交易数据
    def summary(self):
        if self.trader_platform == 1:
            summary_list_new = okx_follow_spider.spider(self.uniqueName, self.follow_type, self.task_id,
                                                        self.trader_platform, self.sums, self.lever_set,
                                                        self.first_order_set, self.api_id, self.user_id)
            return summary_list_new
        else:
            return None

    # 数据分析脚本，连接交易脚本
    def analysis(self, old_list, new_list):
        # 如果没有交易数据，则直接返回
        if not new_list and not old_list:
            return
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
                item['sums'] = self.sums
                item['lever_set'] = self.lever_set
                item['first_order_set'] = self.first_order_set
                item['api_id'] = self.api_id
                item['user_id'] = self.user_id
                # thread_logger.success(
                #     f"交易员{self.uniqueName}进行了开仓操作，品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}")
                self.log_to_database("success", f"交易员{self.uniqueName}进行了开仓操作",
                                     f"品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}")
                # 写入Redis队列
                conn = redis.Redis(**settings.REDIS_PARAMS)
                conn.lpush(settings.TRADE_TASK_NAME, json.dumps(item))


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
                item['sums'] = self.sums
                item['lever_set'] = self.lever_set
                item['first_order_set'] = self.first_order_set
                item['api_id'] = self.api_id
                item['user_id'] = self.user_id
                # thread_logger.success(
                #     f"交易员{self.uniqueName}进行了平仓操作，品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}")
                self.log_to_database("success", f"交易员{self.uniqueName}进行了平仓操作",
                                     f"品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}")
                # 写入Redis队列
                conn = redis.Redis(**settings.REDIS_PARAMS)
                conn.lpush(settings.TRADE_TASK_NAME, json.dumps(item))


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
                          'sums': self.sums,
                          'lever_set': self.lever_set,
                          'first_order_set': self.first_order_set,
                          'api_id': self.api_id,
                          'user_id': self.user_id,
                          }
                changed_items.append(change)
                # thread_logger.success(
                #     f"交易员{self.uniqueName}进行了调仓操作，品种：{old_item['instId']}，原仓位保证金：{round(float(old_item['margin']),2)}USDT，现仓位保证金：{round(float(new_item['margin']),2)}USDT")
                self.log_to_database("success", f"交易员{self.uniqueName}进行了调仓操作",
                                     f"品种：{old_item['instId']}，原仓位保证金：{round(float(old_item['margin']), 2)}USDT，现仓位保证金：{round(float(new_item['margin']), 2)}USDT")
                # 写入Redis队列
                conn = redis.Redis(**settings.REDIS_PARAMS)
                conn.lpush(settings.TRADE_TASK_NAME, json.dumps(change))



