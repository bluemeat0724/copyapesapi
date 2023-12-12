from celery import shared_task
from crawler.account.okx_orderinfo import OkxOrderInfo
from crawler.utils.db import Connect

# 记录日志：
import logging

logger = logging.getLogger("celery")


# 获取正在进行中的任务
def get_tasks():
    with Connect() as db:
        result = db.fetch_all(
            "select id,user_id from api_taskinfo where status = 1")
        return result


@shared_task(name='get_position')
def perform_get_position():
    result = get_tasks()
    if not result:
        return
    for i in result:
        user_id = i.get('user_id')
        task_id = i.get('id')

        order_info = OkxOrderInfo(user_id, task_id)
        order_info.get_position()


if __name__ == '__main__':
    # result = get_tasks()
    # print(result)
    perform_get_position()