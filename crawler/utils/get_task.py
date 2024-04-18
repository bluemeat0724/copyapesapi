import redis
from crawler import settingsprod as settings
from crawler.utils.db import Connect


class DbRow(object):
    def __init__(self, id, trader_platform, uniqueName, follow_type, role_type, reduce_ratio, sums, ratio, lever_set, first_order_set, api_id, user_id,
                 status, create_datetime, deleted, leverage, posSide_set):
        self.id = id
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
        self.status = status
        self.create_datetime = create_datetime
        self.deleted = deleted
        self.leverage = leverage
        self.posSide_set = posSide_set


def get_redis_task():
    conn = redis.Redis(**settings.REDIS_PARAMS)
    try:
        tid = conn.brpop(settings.QUEUE_TASK_NAME, timeout=3)
        if not tid:
            return
        return tid[1].decode('utf-8')
    except:
        return None


def get_task_info_by_id(tid):
    with Connect() as conn:
        row_dict = conn.fetch_one(
            "select id, trader_platform, uniqueName, follow_type, role_type, reduce_ratio, sums, ratio, lever_set, first_order_set, api_id, user_id,status, create_datetime, deleted, leverage, posSide_set from api_taskinfo where id=%(id)s",
            id=tid)

    if not row_dict:
        return
    row_object = DbRow(**row_dict)
    return row_object


def run():
    while 1:
        try:
            # 去redis里获取跟单任务id
            tid = get_redis_task()
            if not tid:
                continue
            # 获取任务信息
            row_object = get_task_info_by_id(tid)
            if not row_object:
                continue
            print(row_object.__dict__)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    run()
