import requests
import json

import redis
from crawler import settings as settings
from crawler.utils.db import Connect


def get_countdown():
    token = get_token()
    url = "https://www.zhizhuip.cc/externalapi/device/accountList"
    params = {
        'access_token': token,
        'type': '2',
        'status': '1',
        'page': '1',
        'pagesize': '10'
    }
    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)'
    }

    response = requests.get(url, params=params, headers=headers)
    data = json.loads(response.text)
    ip_list = data.get('data').get('rows')
    for i in ip_list:
        ip = i.get('ip')
        countdown = float(i.get('countdown').split('天')[0])
        countryName = i.get('countryName')
        username = i.get('username')
        password = i.get('password')

        update_countdown(ip, username, password, countdown, countryName)


def get_token():
    url = "https://www.zhizhuip.cc/externalapi/user/login"
    payload = {
        'account': '15755149931',
        'password': '112233ww'
    }
    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)'
    }

    response = requests.post(url, data=payload, headers=headers)
    data = json.loads(response.text)
    token = data.get('data').get('userinfo').get('token')
    return token


def update_countdown(ip, username, password, countdown, countryName):
    params = {
        'ip': ip,
        'countdown': countdown,
        'countryName': countryName,
        'username': username,
        'password': password
    }
    try:
        update_sql = f"""
                            UPDATE api_ipinfo
                            SET 
                                countdown = %(countdown)s,
                                countryName = %(countryName)s
                            WHERE ip = %(ip)s AND username = %(username)s AND password = %(password)s;
                        """
        with Connect() as db:
            db.exec(update_sql, **params)
        # 如果ip的 countdown < stop 或者
        with Connect() as conn:
            user_dict = conn.fetch_one(
                f"select id from api_ipinfo where ip='{ip}' AND countdown<stop_day and experience_day=0")

            experience_ip_dict = conn.fetch_one(
                f"SELECT id FROM api_ipinfo WHERE ip = '{ip}' AND countdown > 0 AND experience_day > 0 AND created_at < (NOW() - INTERVAL `experience_day` DAY)"
            )

            if user_dict or experience_ip_dict:
                ip_ids = []
                if user_dict:
                    ip_ids.append(user_dict["id"])
                if experience_ip_dict:
                    ip_ids.append(experience_ip_dict["id"])

                if ip_ids:
                    ip_ids_str = "(" + ",".join(map(str, ip_ids)) + ")"
                    query = f"select id from api_taskinfo where ip_id in {ip_ids_str}"
                    tasks = conn.fetch_all(query)

                    if tasks:
                        for item in tasks:
                            # 修改数据库任务状态
                            update_params = {
                                'id': item.get('id'),
                                'status': 3
                            }
                            print(update_params)
                            update_sql = f""" UPDATE api_taskinfo
                                              SET 
                                                status = %(status)s
                                              WHERE id = %(id)s;
                                                    """
                            conn.exec(update_sql, **update_params)

                            # 写入Redis队列，发送redis消费
                            redis_conn = redis.Redis(**settings.REDIS_PARAMS)
                            redis_conn.lpush("TASK_ADD_QUEUE", item["id"])

    except Exception as e:
        print(e)



if __name__ == '__main__':
    get_countdown()
