from crawler.utils.get_proxies import get_my_proxies
from crawler.balance.get_okx_api_balance import get_okx_api_balance
from crawler.utils.db import Connect
from celery import shared_task
from concurrent.futures import ThreadPoolExecutor

# 记录日志：
import logging

logger = logging.getLogger("celery")


def get_tasks():
    with Connect() as conn:
        api_dict = conn.fetch_all(
            "select flag,passPhrase,api_key,secret_key,user_id,id,platform from api_apiinfo WHERE deleted='0'")
        return api_dict

def process_task(task):
    if task == None:
        return
    platform = task.get('platform')
    if platform == 1:
        api_id = task.get('id')
        flag = str(task.get('flag'))
        user_id = task.get('user_id')
        acc = {
            'key': str(task.get('api_key')),
            'secret': str(task.get('secret_key')),
            'passphrase': str(task.get('passPhrase')),
            'proxies': get_my_proxies(user_id, flag)
        }
        get_okx_api_balance(acc, flag, api_id)



@shared_task(name='get_balance')
def perform_get_position():
    result = get_tasks()
    if not result:
        return

    with ThreadPoolExecutor() as executor:
        executor.map(process_task, result)
