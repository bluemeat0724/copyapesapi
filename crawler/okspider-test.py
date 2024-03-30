import datetime
import threading
import time
from crawler.utils.db import Connect
import redis
from crawler import settings as settings
import requests
import json
from loguru import logger
from crawler.utils import get_task

# proxies = {
#     'http': 'socks5h://{}:{}@{}:{}'.format(settings.PROXY_USERNAME, settings.PROXY_PASSWORD, settings.PROXY_IP,
#                                            settings.PROXY_PORT),
#     'https': 'socks5h://{}:{}@{}:{}'.format(settings.PROXY_USERNAME, settings.PROXY_PASSWORD, settings.PROXY_IP,
#                                             settings.PROXY_PORT),
#     # 'https': 'socks5h://15755149931sct-5:8ivtkleb@38.147.173.111:5003'
#     # 'all': 'socks5h://15755149931sct-5:8ivtkleb@38.147.173.111:5003'
# }

header = {
    "user-agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
}

now = int(time.time()) * 1000

logger.remove()  # 移除所有默认的handler


class Spider(threading.Thread):
    def __init__(self, task_id, trader_platform, uniqueName, follow_type, sums, lever_set, first_order_set, api_id,
                 user_id, leverage, posSide_set):
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
        self.leverage = leverage
        self.posSide_set = posSide_set
        self.stop_flag = threading.Event()  # 用于控制爬虫线程的停止

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
                        INSERT INTO api_spiderlog (user_id, task_id, date, color, title, description, created_at, updated_at)
                        VALUES (%(user_id)s, %(task_id)s, %(date)s, %(color)s, %(title)s, %(description)s, NOW(), NOW())
                    """
        with Connect() as db:
            db.exec(insert_sql, **params)

    def run(self):
        self.log_to_database("INFO", f"跟单猿跟单系统启动", f"跟随交易员：{self.uniqueName}")
        # 第一次获取当前交易数据
        old_list = self.test()
        if old_list:
            # thread_logger.INFO(f"交易员{self.uniqueName}有正在进行中的交易，等待新的交易发生后开始跟随！")
            # thread_logger.debug(old_list)
            self.log_to_database("INFO", f"交易员{self.uniqueName}有正在进行中的交易", "等待新的交易发生后开始跟随！")
        else:
            # thread_logger.INFO(f"交易员{self.uniqueName}尚未开始交易，等待新的交易发生后开始跟随！")
            self.log_to_database("INFO", f"交易员{self.uniqueName}尚未开始交易", "等待新的交易发生后开始跟随！")
        while not self.stop_flag.is_set():
            new_list = self.test()
            self.analysis(old_list, new_list)
            old_list = new_list
            time.sleep(1)

    def stop(self):
        # 设置停止标志，用于停止爬虫线程
        self.stop_flag.set()
        # self.thread_logger.WARNING(f"手动结束跟单，任务ID：{self.task_id}")
        self.log_to_database("WARNING", "手动结束跟单", f"任务ID：{self.task_id}")

    # 创建一个线程锁
    file_lock = threading.Lock()

    def test(self):
        summary_list_new = []
        with self.file_lock:
            with open('text.txt', 'r') as f:
                data_list = json.loads(f.read())
        if not data_list:
            return summary_list_new
        for data in data_list:
            data_clear = {}
            data_clear['margin'] = data.get('margin')
            data_clear['availSubPos'] = float(data.get('availSubPos'))
            data_clear['instId'] = data.get('instId')
            data_clear['mgnMode'] = data.get('mgnMode')
            data_clear['posSide'] = data.get('posSide')
            data_clear['lever'] = data.get('lever')
            data_clear['openTime'] = data.get('openTime')
            data_clear['openAvgPx'] = data.get('openAvgPx')
            data_clear['task_id'] = self.task_id
            data_clear['trader_platform'] = self.trader_platform
            data_clear['follow_type'] = self.follow_type
            data_clear['uniqueName'] = self.uniqueName
            data_clear['sums'] = self.sums
            data_clear['lever_set'] = self.lever_set
            data_clear['first_order_set'] = self.first_order_set
            data_clear['api_id'] = self.api_id
            data_clear['user_id'] = self.user_id
            summary_list_new.append(data_clear)
        return summary_list_new

    def summary(self):
        summary_list_new = []
        url = f'https://www.okx.com/priapi/v5/ecotrade/public/position-summary?t={now}&uniqueName={self.uniqueName}&instType=SWAP'
        try:
            data_list = requests.get(url, headers=header, timeout=30).json().get('data', list())
            if not data_list:
                return summary_list_new

            for data in data_list:
                data_clear = {}
                data_clear['margin'] = data.get('margin')
                # data_clear['notionalUsd'] = data.get('notionalUsd')
                data_clear['instId'] = data.get('instId')
                data_clear['mgnMode'] = data.get('mgnMode')
                data_clear['posSide'] = data.get('posSide')
                data_clear['lever'] = data.get('lever')
                data_clear['openTime'] = data.get('openTime')
                data_clear['openAvgPx'] = data.get('openAvgPx')
                data_clear['task_id'] = self.task_id
                data_clear['trader_platform'] = self.trader_platform
                data_clear['follow_type'] = self.follow_type
                data_clear['uniqueName'] = self.uniqueName
                data_clear['sums'] = self.sums
                data_clear['lever_set'] = self.lever_set
                data_clear['first_order_set'] = self.first_order_set
                data_clear['api_id'] = self.api_id
                data_clear['user_id'] = self.user_id
                summary_list_new.append(data_clear)
            return summary_list_new
        except:
            pass

    def transform(self, item):
        item['posSide_set'] = self.posSide_set
        if item.get("lever_set", None):
            if item["lever_set"] == 2:
                item["lever"] = self.leverage
        return item

    def analysis(self, old_list, new_list):
        # 查找新增的交易数据
        name_set = set(i['instId'] for i in old_list)
        added_items = list(filter(lambda x: x['instId'] not in name_set, new_list))
        # logger.debug('added_items:',added_items)
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
                item = self.transform(item)
                # thread_logger.success(f"交易员{self.uniqueName}进行了开仓操作，品种：{item['instId']}，杠杆：{item['lever']}")
                self.log_to_database("success", f"交易员{self.uniqueName}进行了开仓操作",
                                     f"品种：{item['instId']}，杠杆：{item['lever']}")
                # 写入Redis队列

                conn = redis.Redis(**settings.REDIS_PARAMS)
                conn.lpush(settings.TRADE_TASK_NAME, json.dumps(item))
            # return added_items

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
                item = self.transform(item)
                # self.thread_logger.success(
                #     f"交易员{self.uniqueName}进行了平仓操作，品种：{item['instId']}，杠杆：{item['lever']}")
                self.log_to_database("success", f"交易员{self.uniqueName}进行了平仓操作",
                                     f"品种：{item['instId']}，杠杆：{item['lever']}")
                # 写入Redis队列
                conn = redis.Redis(**settings.REDIS_PARAMS)
                conn.lpush(settings.TRADE_TASK_NAME, json.dumps(item))
            # return removed_items

        # 查找值变化的数据
        changed_items = []
        for old_item, new_item in zip(old_list, new_list):
            if old_item["instId"] == new_item["instId"] and old_item['margin'] != new_item['margin']:
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
                change = self.transform(change)
                changed_items.append(change)
                self.log_to_database("success", f"交易员{self.uniqueName}进行了调仓操作",
                                     f"品种：{old_item['instId']}，原仓位：{old_item['margin']}，现仓位：{new_item['margin']}")
                # thread_logger.success(
                #     f"交易员{self.uniqueName}进行了调仓操作，品种：{old_item['instId']}，原仓位：{old_item['margin']}，现仓位：{new_item['margin']}")
                # 写入Redis队列
                conn = redis.Redis(**settings.REDIS_PARAMS)
                conn.lpush(settings.TRADE_TASK_NAME, json.dumps(change))
        return added_items, removed_items, changed_items


# 用字典映射任务ID和爬虫实例
spiders = {}

if __name__ == '__main__':
    while True:
        try:
            # 去redis里获取跟单任务id
            tid = get_task.get_redis_task()
            if not tid:
                continue
            # 获取任务信息
            row_object = get_task.get_task_info_by_id(tid)
            if not row_object:
                continue
            task_data = row_object.__dict__  # 解析任务的字典
            task_id = task_data.get('id')
            trader_platform = task_data.get('trader_platform')
            uniqueName = task_data.get('uniqueName')
            follow_type = task_data.get('follow_type')
            sums = task_data.get('sums')
            lever_set = task_data.get('lever_set')
            first_order_set = task_data.get('first_order_set')
            api_id = task_data.get('api_id')
            status = task_data.get('status')
            user_id = task_data.get('user_id')
            leverage = task_data.get('leverage')
            posSide_set = task_data.get('posSide_set')

            if status == 1:
                # 开启新爬虫
                if task_id not in spiders:
                    spider = Spider(task_id, trader_platform, uniqueName, follow_type, sums, lever_set, first_order_set,
                                    api_id, user_id, leverage, posSide_set)
                    spider.start()
                    spiders[task_id] = spider
                    print(f"用户：{user_id}的最新跟单任务{task_id}已经开始。")
                else:
                    print(f"用户：{user_id}的跟单任务{task_id}已存在。")

            elif status == 2:
                # 终止爬虫
                if task_id in spiders:
                    spider_to_stop = spiders[task_id]
                    spider_to_stop.stop()
                    spider_to_stop.join()
                    # 往redis里的TRADE_TASK_NAME写入{'task_id':task_id,'status': 2}
                    conn = redis.Redis(**settings.REDIS_PARAMS)
                    conn.lpush(settings.TRADE_TASK_NAME, json.dumps({'task_id': task_id, 'status': 2}))
                    del spiders[task_id]
                    print(f"用户：{user_id}的跟单任务{task_id}已停止。")
                else:
                    print(f"用户：{user_id}的跟单任务{task_id}不存在")

        except (SyntaxError, NameError):
            print("数据错误！")

# 当需要退出程序时，你可以在控制台输入Ctrl+C 来中断程序运行。{'id': 2, 'status': 1}{'id': 1, 'status': 1}
