from crawler.spiders import app
from crawler.utils import get_task
from crawler.utils.reactivate_tasks import reactivate_tasks
from crawler import settingsprod as settings
import redis
import json

# 用字典映射任务ID和爬虫实例
spiders = {}


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

            if status == 1:
                # 开启新爬虫
                if task_id not in spiders:
                    spider = app.Spider(task_id, trader_platform, uniqueName, follow_type, role_type, reduce_ratio,sums, ratio, lever_set,
                                        first_order_set, api_id, user_id, leverage, posSide_set, fast_mode)
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
                    spider_to_stop.join()
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

        except (SyntaxError, NameError):
            print("数据错误！")


if __name__ == '__main__':
    run()
