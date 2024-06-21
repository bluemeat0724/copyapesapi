from crawler.spiders import app
from crawler.utils import get_task
from crawler.utils.reactivate_tasks import reactivate_tasks
from crawler import settingsdev as settings
import redis
import json

import threading
import time
import datetime


# 定义保活检查间隔（秒）
KEEP_ALIVE_INTERVAL = 60
# 用字典映射任务ID和爬虫实例
spiders = {}

# 保活检查
def keep_spiders_alive():
    while True:
        for task_id, spider in list(spiders.items()):
            if spider.is_alive():  # 如果爬虫线程仍然活跃
                pass
                # print(f"任务 {task_id} 的爬虫仍然活跃。")
            else:  # 如果爬虫线程不再活跃
                print(f"{datetime.datetime.now()}，任务 {task_id} 的爬虫不再活跃，尝试重新启动。")
                # 重新启动爬虫
                new_spider = app.Spider(spider.task_id, spider.trader_platform, spider.uniqueName, spider.follow_type, spider.role_type,
                                        spider.reduce_ratio, spider.sums, spider.ratio, spider.lever_set, spider.first_order_set,
                                        spider.api_id, spider.user_id, spider.leverage, spider.posSide_set, spider.fast_mode, spider.investment, spider.trade_trigger_mode, spider.sl_trigger_px, spider.sl_trigger_px,
                                        spider.first_open_type, spider.uplRatio)
                new_spider.start()
                spiders[task_id] = new_spider
        time.sleep(KEEP_ALIVE_INTERVAL)

def run():
    """
    {'id': 1, 'status': 2}：开启任务1
    {'id': 1, 'status': 2}：终止任务1
    """
    # 查看taskinfo表，看是否有需要恢复的任务
    reactivate_tasks()

    # 进入主程序
    while True:
        try:
            # 去redis里获取跟单任务id
            tid = get_task.get_redis_task()
            if not tid:
                continue
            # 从mysql获取任务信息
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
            investment = task_data.get('investment')
            trade_trigger_mode = task_data.get('trade_trigger_mode')
            sl_trigger_px = task_data.get('sl_trigger_px')
            tp_trigger_px = task_data.get('tp_trigger_px')
            first_open_type = task_data.get('first_open_type')
            uplRatio = task_data.get('uplRatio')

            if status == 1:
                # 开启新爬虫
                if task_id not in spiders:
                    spider = app.Spider(task_id, trader_platform, uniqueName, follow_type, role_type, reduce_ratio,sums, ratio, lever_set,
                                        first_order_set, api_id, user_id, leverage, posSide_set, fast_mode, investment, trade_trigger_mode, sl_trigger_px, tp_trigger_px, first_open_type, uplRatio)
                    spider.start()
                    spiders[task_id] = spider
                    print(f"用户：{user_id}的最新跟单任务{task_id}已经开始。")
                else:
                    print(f"用户：{user_id}的跟单任务{task_id}已存在。")

            elif status in [2, 3]:
                # 终止爬虫
                if task_id in spiders:
                    spider_to_stop = spiders[task_id]
                    spider_to_stop.status = status
                    spider_to_stop.stop()
                    spider_to_stop.join(timeout=10)
                    # 组装数据
                    task_data['task_id'] = task_data.pop('id')
                    task_data.pop("create_datetime")
                    task_data.pop("deleted")
                    task_data.pop("leverage")
                    del spiders[task_id]
                    # 往redis里的TRADE_TASK_NAME写入{'task_id':task_id,'status': 2}
                    conn = redis.Redis(**settings.REDIS_PARAMS)
                    conn.lpush(settings.TRADE_TASK_NAME, json.dumps(task_data))
                    if status == 2:
                        print(f"用户：{user_id}的跟单任务{task_id}已停止。")
                    elif status == 3:
                        print(f"IP即将过期。用户：{user_id}的跟单任务{task_id}已停止。")
                else:
                    print(f"用户：{user_id}的跟单任务{task_id}不存在")
        except Exception as e:
            print(e)
            print(f'{datetime.datetime.now()}，程序异常退出。')


if __name__ == '__main__':
    # 启动保活线程
    keep_alive_thread = threading.Thread(target=keep_spiders_alive)
    keep_alive_thread.daemon = True  # 设置为守护线程，当主线程结束时自动退出
    keep_alive_thread.start()
    run()