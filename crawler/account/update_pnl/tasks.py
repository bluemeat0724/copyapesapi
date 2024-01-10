from crawler.account.update_total_pnl import update_api_pnl, update_user_pnl
from crawler.utils.db import Connect
from concurrent.futures import ThreadPoolExecutor
from celery import shared_task

# 记录日志：
import logging

logger = logging.getLogger("celery")


# 获取每个用的每个api
def get_tasks():
    with Connect() as db:
        user_result = db.fetch_all(
            "select id from api_userinfo where status = 1")
        id_list = [item['id'] for item in user_result]
        return id_list

def process_task(user_id):
    with Connect() as db:
        api_result = db.fetch_all(
            "select id from api_apiinfo where user_id = %(user_id)s", user_id=user_id)
        if not api_result:
            return
        for item in api_result:
            api_id = item['id']
            update_api_pnl(api_id)
            update_user_pnl(user_id)


@shared_task(name='update_pnl')
def perform_update_pnl():
    result = get_tasks()
    if not result:
        return

    with ThreadPoolExecutor() as executor:
        executor.map(process_task, result)


if __name__ == '__main__':
    process_task(16)