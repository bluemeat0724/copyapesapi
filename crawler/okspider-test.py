import datetime
import threading
import time
from crawler.utils.db import Connect
import redis
from crawler import settingsprod as settings
import requests
import json
from loguru import logger
from crawler.utils import get_task
from crawler.utils.reactivate_tasks import reactivate_tasks

# proxies = {
#     'http': 'socks5h://{}:{}@{}:{}'.format(settings.PROXY_USERNAME, settings.PROXY_PASSWORD, settings.PROXY_IP,
#                                            settings.PROXY_PORT),
#     'https': 'socks5h://{}:{}@{}:{}'.format(settings.PROXY_USERNAME, settings.PROXY_PASSWORD, settings.PROXY_IP,
#                                             settings.PROXY_PORT),
#     # 'https': 'socks5h://15755149931sct-5:8ivtkleb@18.167.134.231:5003'
#     # 'all': 'socks5h://15755149931sct-5:8ivtkleb@18.167.134.231:5003'
# }

header = {
    "user-agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
}

now = int(time.time()) * 1000

logger.remove()  # 移除所有默认的handler


class Spider(threading.Thread):
    def __init__(self, task_id, trader_platform, uniqueName, follow_type, role_type, reduce_ratio, sums, ratio, lever_set, first_order_set, api_id,
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
        self.fast_mode = fast_mode
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
            time.sleep(2)

    def stop(self):
        # 设置停止标志，用于停止爬虫线程
        self.stop_flag.set()
        # self.thread_logger.WARNING(f"手动结束跟单，任务ID：{self.task_id}")
        self.log_to_database("WARNING", "手动结束跟单", f"任务ID：{self.task_id}")

    # 创建一个线程锁
    file_lock = threading.Lock()

    def test(self):
        summary_list_new = []
        if self.role_type == 1:
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
                data_clear['ratio'] = self.ratio
                data_clear['lever_set'] = self.lever_set
                data_clear['first_order_set'] = self.first_order_set
                data_clear['api_id'] = self.api_id
                data_clear['user_id'] = self.user_id
                data_clear['fast_mode'] = self.fast_mode
                summary_list_new.append(data_clear)
            return summary_list_new

        elif self.role_type == 2:
            data_clear = {}
            with self.file_lock:
                with open('text_personal.txt', 'r') as f:
                    data_list = json.loads(f.read())
            if not data_list:
                return summary_list_new
            with self.file_lock:
                with open('text_record.txt', 'r') as f:
                    record_list = json.loads(f.read())
            data_clear['instId'] = record_list[0].get('instId')
            data_clear['openTime'] = record_list[0].get('cTime')  # 用于判断是否是最新的交易记录
            data_clear['posSide'] = record_list[0].get('posSide')
            data_clear['lever'] = record_list[0].get('lever')
            data_clear['openAvgPx'] = record_list[0].get('avgPx')
            exist = False
            for item in data_list:
                if item.get('instId') == record_list[0].get('instId') and item.get('posSide') == record_list[0].get(
                        'posSide'):
                    data_clear['mgnMode'] = item.get('mgnMode')
                    exist = True
                    if record_list[0].get('side') == 'buy':
                        data_clear['order_type'] = 'open'
                    else:
                        data_clear['order_type'] = 'reduce'  # 减仓
            if not exist:
                data_clear['order_type'] = 'close'  # 平仓
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
                data_clear['ratio'] = self.ratio
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
        if self.role_type == 1:
            self.analysis_1(old_list, new_list)
        elif self.role_type == 2:
            self.analysis_2(old_list, new_list)

    def analysis_1(self, old_list, new_list):
        # 查找新增的交易数据
        # 将旧列表中的(instId, mgnMode)对存入集合
        old_set = set((i['instId'], i['mgnMode']) for i in old_list)
        # 使用(instId, mgnMode)对来判断新列表中的新增项
        added_items = list(filter(lambda x: (x['instId'], x['mgnMode']) not in old_set, new_list))
        # logger.debug('added_items:',added_items)
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
                # thread_logger.success(f"交易员{self.uniqueName}进行了开仓操作，品种：{item['instId']}，杠杆：{item['lever']}")
                self.log_to_database("success", f"交易员{self.uniqueName}进行了开仓操作",
                                     f"品种：{item['instId']}，杠杆：{item['lever']}")
                # 写入Redis队列
                print('open',json.dumps(item))
                conn = redis.Redis(**settings.REDIS_PARAMS)
                conn.lpush(settings.TRADE_TASK_NAME, json.dumps(item))
            # return added_items

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
                item = self.transform(item)
                # self.thread_logger.success(
                #     f"交易员{self.uniqueName}进行了平仓操作，品种：{item['instId']}，杠杆：{item['lever']}")
                self.log_to_database("success", f"交易员{self.uniqueName}进行了平仓操作",
                                     f"品种：{item['instId']}，杠杆：{item['lever']}")
                print('close',json.dumps(item))
                # 写入Redis队列
                conn = redis.Redis(**settings.REDIS_PARAMS)
                conn.lpush(settings.TRADE_TASK_NAME, json.dumps(item))
            # return removed_items

        # 查找值变化的数据
        changed_items = []
        for old_item, new_item in zip(old_list, new_list):
            if old_item["instId"] == new_item["instId"] and old_item["mgnMode"] == new_item["mgnMode"] and old_item['margin'] != new_item['margin']:
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
                          'fast_mode':self.fast_mode
                          }
                change = self.transform(change)
                changed_items.append(change)
                print('change',change)
                self.log_to_database("success", f"交易员{self.uniqueName}进行了调仓操作",
                                     f"品种：{old_item['instId']}，原仓位：{old_item['margin']}，现仓位：{new_item['margin']}")
                # thread_logger.success(
                #     f"交易员{self.uniqueName}进行了调仓操作，品种：{old_item['instId']}，原仓位：{old_item['margin']}，现仓位：{new_item['margin']}")
                # 写入Redis队列
                conn = redis.Redis(**settings.REDIS_PARAMS)
                conn.lpush(settings.TRADE_TASK_NAME, json.dumps(change))


    def analysis_2(self, old_list, new_list):
        # 如果没有当前持仓数据，则直接返回
        if not new_list and not old_list:
            return

        # 如果cTime时间不一样，说明有新的交易动作
        if not old_list or old_list[0]['openTime'] != new_list[0]['openTime']:
            if new_list[0]['order_type'] == 'open':
                self.log_to_database("success", f"交易员{self.uniqueName}进行了开仓或加仓操作",
                                     f"品种：{new_list[0]['instId']}，杠杆：{new_list[0]['lever']}，方向：{new_list[0]['posSide']}")
            elif new_list[0]['order_type'] == 'close':
                self.log_to_database("success", f"交易员{self.uniqueName}进行了平仓操作",
                                     f"品种：{new_list[0]['instId']}，杠杆：{new_list[0]['lever']}，方向：{new_list[0]['posSide']}")
            elif new_list[0]['order_type'] == 'reduce':
                self.log_to_database("success", f"交易员{self.uniqueName}进行了减仓操作",
                                     f"品种：{new_list[0]['instId']}，杠杆：{new_list[0]['lever']}，方向：{new_list[0]['posSide']}")

            # 补全任务数据
            new_list[0]['task_id'] = self.task_id
            new_list[0]['trader_platform'] = self.trader_platform
            new_list[0]['follow_type'] = self.follow_type
            new_list[0]['uniqueName'] = self.uniqueName
            new_list[0]['role_type'] = self.role_type
            new_list[0]['reduce_ratio'] = self.reduce_ratio
            new_list[0]['sums'] = self.sums
            new_list[0]['ratio'] = self.ratio
            new_list[0]['lever_set'] = self.lever_set
            new_list[0]['first_order_set'] = self.first_order_set
            new_list[0]['api_id'] = self.api_id
            new_list[0]['user_id'] = self.user_id
            if new_list[0]['order_type'] == 'close':
                # TODO 只能拿上一条记录的mgnMode，如果有全仓和逐仓同时出现的交易就有拿错的风险
                new_list[0]['mgnMode'] = old_list[0].get('mgnMode', 'cross')
            # 重新设置杠杆
            item = self.transform(new_list[0])
            # 写入Redis队列
            conn = redis.Redis(**settings.REDIS_PARAMS)
            conn.lpush(settings.TRADE_TASK_NAME, json.dumps(item))


# 用字典映射任务ID和爬虫实例
spiders = {}

if __name__ == '__main__':
    # 查看taskinfo表，看是否有需要恢复的任务
    reactivate_tasks()
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
            role_type = task_data.get('role_type')
            reduce_ratio = task_data.get('reduce_ratio')
            sums = task_data.get('sums')
            ratio = task_data.get('ratio')
            lever_set = task_data.get('lever_set')
            first_order_set = task_data.get('first_order_set')
            api_id = task_data.get('api_id')
            status = task_data.get('status')
            user_id = task_data.get('user_id')
            leverage = task_data.get('leverage')
            posSide_set = task_data.get('posSide_set')
            fast_mode = task_data.get('fast_mode')

            if status == 1:
                # 开启新爬虫
                if task_id not in spiders:
                    spider = Spider(task_id, trader_platform, uniqueName, follow_type,role_type,reduce_ratio, sums, ratio, lever_set, first_order_set,
                                    api_id, user_id, leverage, posSide_set, fast_mode)
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
                    # 组装数据
                    task_data['task_id'] = task_data.pop('id')
                    task_data.pop("create_datetime")
                    task_data.pop("deleted")
                    task_data.pop("leverage")
                    # print(task_data)
                    # 往redis里的TRADE_TASK_NAME写入{'task_id':task_id,'status': 2}
                    conn = redis.Redis(**settings.REDIS_PARAMS)
                    conn.lpush(settings.TRADE_TASK_NAME, json.dumps(task_data))
                    del spiders[task_id]
                    print(f"用户：{user_id}的跟单任务{task_id}已停止。")
                else:
                    print(f"用户：{user_id}的跟单任务{task_id}不存在")

        except (SyntaxError, NameError):
            print("数据错误！")

# 当需要退出程序时，你可以在控制台输入Ctrl+C 来中断程序运行。{'id': 2, 'status': 1}{'id': 1, 'status': 1}
