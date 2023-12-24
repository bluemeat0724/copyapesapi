from crawler.utils.db import Connect
import redis
from crawler import settingsdev as settings


def reactivate_tasks():
    """
    获取所有status=1的任务
    手动lpush进redis
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
            print(f"任务{task_id}已恢复")


if __name__ == '__main__':
    reactivate_task()
