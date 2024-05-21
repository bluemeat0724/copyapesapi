from crawler.utils.db import Connect
from crawler.utils.get_api import api
from crawler.myokx import app


def get_api_id(task_id):
    with Connect() as conn:
        result = conn.fetch_one("select api_id from api_taskinfo where id = %(id)s", id={task_id})
        return result.get('api_id') if result else None

def get_position(user_id, task_id):
    api_id = get_api_id(task_id)
    acc, flag, ip_id = api(user_id, api_id)

    obj = app.OkxSWAP(**acc)
    obj.account.api.flag = flag
    data = obj.account.get_positions().get('data')
    return data




if __name__ == '__main__':
    print(get_position(1, 388))
