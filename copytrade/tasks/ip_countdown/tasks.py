import json
from celery import shared_task
from crawler.utils.db import Connect



# 记录日志：
import logging

logger = logging.getLogger("celery")



@shared_task(name='ip_countdown')
def ip_countdown():
    with Connect() as db:
        # 查询所有 countdown 大于 0 的记录
        result = db.fetch_all("SELECT id, countdown, ip, user_id FROM api_ipinfo WHERE countdown > 0")

        # 更新 countdown 值并保存回数据库
        for row in result:
            ip_id = row['id']
            countdown_value = row['countdown']

            # 更新 countdown 值减 1
            new_countdown_value = countdown_value - 1

            # 保存更新后的值回数据库
            sql = f"UPDATE api_ipinfo SET countdown = {new_countdown_value} WHERE id = {ip_id}"
            db.exec(sql)

            # 如果ip有效期归零，则刷新代理统计数据
            # todo 终止该用户正在进行中的任务 可从updata_ip_countdown里找到
            if new_countdown_value == 0:
                ip = row['ip']
                user_id = row['user_id']
                proxy_renew(ip, user_id)

def proxy_renew(ip, user_id):
    """
    代理统计刷新
    代理使用用户数-1，用户列表删除该用户
    """
    with Connect() as db:
        result = db.fetch_one(f"SELECT * FROM api_proxyinfo WHERE ip='{ip}'")
        count = result['count'] - 1
        user_list = json.loads(result['user_list'])
        if user_id in user_list:
            user_list.remove(user_id)
        sql = f"UPDATE api_proxyinfo SET count = {count}, user_list = '{json.dumps(user_list)}' WHERE ip='{ip}'"
        db.exec(sql)


if __name__ == '__main__':
    ip_countdown()
    # proxy_renew('1.1.1.1', 1)