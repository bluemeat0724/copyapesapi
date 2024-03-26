import requests
import json
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
    except:
        pass



if __name__ == '__main__':
    get_countdown()
