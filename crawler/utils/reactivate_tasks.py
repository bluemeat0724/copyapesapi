from crawler.utils.db import Connect
import redis
from crawler import settings as settings


def reactivate_tasks():
    """
    获取所有status=1的任务
    第一步：手动lpush进redis，恢复爬虫任务
    """
    # 获取task_id
    with Connect() as db:
        result = db.fetch_all("SELECT id FROM api_taskinfo WHERE status = 1")
        if not result:
            print("没有需要恢复的任务")
            return
        for item in result:
            task_id = item['id']
            # 往redis里的QUEUE_TASK_NAME写入task_id
            conn = redis.Redis(**settings.REDIS_PARAMS)
            conn.lpush(settings.QUEUE_TASK_NAME, task_id)
            print(f"任务{task_id}爬虫已恢复")


def reactivate_trade_tasks():
    """
    第二步：恢复交易实例
    获取所有status=1的任务，以及对应的api信息，封装成实例列表返回。
    trade app在接收到实例列表后，在推送到用来映射任务ID和交易实例的字典里traders = {}
    """
    with Connect() as db:
        result = db.fetch_all(
            "SELECT id, api_id,user_id, trader_platform, uniqueName, follow_type, sums, lever_set, first_order_set, posSide_set FROM api_taskinfo WHERE status = 1")
        if not result:
            print("没有需要恢复的任务")
            return
    # 数据结构转换，交由trade app处理
    for d in result:
        d['task_id'] = d.pop('id')
    return result



if __name__ == '__main__':
    reactivate_trade_tasks()
