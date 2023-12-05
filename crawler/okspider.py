import threading
import time
from utils import get_task
import redis
import settings
import requests
import json
from loguru import logger
import random
from utils.db import Connect


now = int(time.time()) * 1000

logger.remove()  # 移除所有默认的handler

def thread_log_filter(record, user_id, task_id):
    """过滤器，只接收包含特定线程标记的日志记录"""
    return record["extra"].get("user_id") == user_id and record["extra"].get("task_id") == task_id

class Spider(threading.Thread):
    def __init__(self, task_id, trader_platform, uniqueName, follow_type, sums, lever_set, first_order_set, api_id,
                 user_id,):
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
        self.thread_logger = None

    def setup_logger(self):
        log_file = f"spider_logs/{self.user_id}_{self.task_id}.log"

        # 为当前线程创建一个标记过滤器
        filter_func = lambda record: thread_log_filter(record, self.user_id, self.task_id)

        # 添加一个新的文件handler，仅接收当前线程的日志消息
        logger.add(log_file, filter=filter_func, rotation="20 MB",
                   format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

    def run(self):
        self.setup_logger()
        thread_logger = logger.bind(user_id=self.user_id, task_id=self.task_id)
        self.thread_logger = thread_logger
        thread_logger.info(f"跟单猿跟单系统启动，跟随交易员：{self.uniqueName}")
        # 第一次获取当前交易数据
        old_list = self.summary(self.uniqueName)
        if old_list:
            thread_logger.info(f"交易员{self.uniqueName}有正在进行中的交易，等待新的交易发生后开始跟随！")
            # thread_logger.debug(old_list)
        else:
            thread_logger.info(f"交易员{self.uniqueName}尚未开始交易，等待新的交易发生后开始跟随！")

        # 断线次数
        count = 0
        # 是否打印日志的标记
        log_print = True
        # 网络超时判断
        timeout = False

        while not self.stop_flag.is_set():
            try:
                new_list = self.summary(self.uniqueName)
                # 网络恢复
                if timeout:
                    timeout = False
                    thread_logger.success("网络恢复")
                    count = 0  # 重置计数器
                    log_print = True  # 重置日志打印标记

                self.analysis(old_list, new_list, thread_logger)
                old_list = new_list
            except:
                timeout = True
                count += 1
                if count <= 3 and log_print:
                    thread_logger.warning(f"网络中断，正在尝试重新连接网络...")
                elif count > 3 and log_print:
                    log_print = False  # 超过3次后停止打印日志

                time.sleep(10)
                continue

            time.sleep(1)

    def stop(self):
        # 设置停止标志，用于停止爬虫线程
        self.stop_flag.set()
        self.thread_logger.warning(f"手动结束跟单，任务ID：{self.task_id}")

    def summary(self, uniqueName):
        summary_list_new = []
        url = f'https://www.okx.com/priapi/v5/ecotrade/public/position-summary?t={now}&uniqueName={uniqueName}&instType=SWAP'
        try:
            data_list = requests.get(url, headers=self.get_proxies(), proxies=self.get_proxies(), timeout=30).json().get('data', list())
            if not data_list:
                return summary_list_new

            for data in data_list:
                data_clear = {}
                data_clear['availSubPos'] = data.get('availSubPos')
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
            self.timeout = True

    # 动态ip
    def get_proxies(self):
        with Connect() as conn:
            PROXY_DICT = conn.fetch_all("select username,password from api_ipinfo where countdown>0")

        proxies_account = random.choice(PROXY_DICT)

        proxies = {
            'http': 'socks5h://{}:{}@{}:{}'.format(proxies_account['username'], proxies_account['password'],
                                                   settings.PROXY_IP,
                                                   settings.PROXY_PORT),
            'https': 'socks5h://{}:{}@{}:{}'.format(proxies_account['username'], proxies_account['password'],
                                                    settings.PROXY_IP,
                                                    settings.PROXY_PORT),
            # 'https': 'socks5h://15755149931sct-5:8ivtkleb@38.147.173.111:5003'
            # 'all': 'socks5h://15755149931sct-5:8ivtkleb@38.147.173.111:5003'
        }
        return proxies

    # 动态header
    def get_header(self):
        user_agent = random.choice(settings.USER_AGENTS)
        header = {
            "user-agent": user_agent
        }
        return header

    def analysis(self, old_list, new_list, thread_logger):
        # 查找新增的交易数据
        name_set = set(i['instId'] for i in old_list)
        added_items = list(filter(lambda x: x['instId'] not in name_set, new_list))
        # added_items = list(filter(lambda x: x['instId'] not in name_set if x is not None else False, new_list))
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
                thread_logger.success(f"交易员{self.uniqueName}进行了开仓操作，品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}")
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
                thread_logger.success(
                    f"交易员{self.uniqueName}进行了平仓操作，品种：{item['instId']}，杠杆：{item['lever']}，方向：{item['posSide']}")
                # 写入Redis队列
                conn = redis.Redis(**settings.REDIS_PARAMS)
                conn.lpush(settings.TRADE_TASK_NAME, json.dumps(item))
            # return removed_items

        # 查找值变化的数据
        changed_items = []
        for old_item, new_item in zip(old_list, new_list):
            if old_item["instId"] == new_item["instId"] and old_item['availSubPos'] != new_item['availSubPos']:
                change = {'order_type': 'change',
                          'instId': old_item['instId'],
                          'old_availSubPos': old_item['availSubPos'],
                          'new_availSubPos': new_item['availSubPos'],
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
                thread_logger.success(
                    f"交易员{self.uniqueName}进行了调仓操作，品种：{old_item['instId']}，原仓位：{old_item['availSubPos']}USDT，现仓位：{new_item['availSubPos']}USDT")
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

            if status == 1:
                # 开启新爬虫
                if task_id not in spiders:
                    spider = Spider(task_id, trader_platform, uniqueName, follow_type, sums, lever_set, first_order_set,
                                    api_id, user_id)
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
                    del spiders[task_id]
                    # 往redis里的TRADE_TASK_NAME写入{'task_id':task_id,'status': 2}
                    conn = redis.Redis(**settings.REDIS_PARAMS)
                    conn.lpush(settings.TRADE_TASK_NAME, json.dumps({'task_id': task_id, 'status': 2}))
                    print(f"用户：{user_id}的跟单任务{task_id}已停止。")
                else:
                    print(f"用户：{user_id}的跟单任务{task_id}不存在")

        except (SyntaxError, NameError):
            print("数据错误！")

# 当需要退出程序时，你可以在控制台输入Ctrl+C 来中断程序运行。{'id': 2, 'status': 1}{'id': 1, 'status': 1}
