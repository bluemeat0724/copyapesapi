from crawler.utils.db import Connect
from crawler import settingsprod as settings
import random


# 随机获取所有用户的代理，用于爬虫
def get_proxies():
    with Connect() as conn:
        PROXY_DICT = conn.fetch_all("select username,password,id from api_ipinfo where countdown>0 AND experience_day=0")
        # print(PROXY_DICT)

    proxies_account = random.choice(PROXY_DICT)

    proxies = {
        'http': 'socks5h://{}:{}@{}:{}'.format(proxies_account['username'], proxies_account['password'],
                                               settings.PROXY_IP,
                                               settings.PROXY_PORT),
        'https': 'socks5h://{}:{}@{}:{}'.format(proxies_account['username'], proxies_account['password'],
                                                settings.PROXY_IP,
                                                settings.PROXY_PORT)
        # 'all': 'socks5h://15755149931sct-5:8ivtkleb@38.147.173.111:5003'
    }
    return proxies, proxies_account['id']


# 获取用户自己的代理，用于交易
def get_my_proxies(user_id, flag):
    with Connect() as conn:
        ip_dict = conn.fetch_one(
            "select username,password,id from api_ipinfo where user_id=%(user_id)s AND countdown>0 AND experience_day=0",
            user_id={user_id})

    with Connect() as conn:
        experience_ip_dict = conn.fetch_one(
            "select username,password,id from api_ipinfo where user_id=%(user_id)s AND countdown>0 AND experience_day>0 AND created_at > (NOW() - INTERVAL 15 DAY)",
            user_id={user_id})
    # print(ip_dict)
    # print(experience_ip_dict)
    # 如果用户用模拟盘测试，但没有提供固定ip，则随机选择一个ip给用户使用
    ip_id = None
    if ip_dict is None:
        if experience_ip_dict is None:
            if flag == '1':
                proxies, ip_id = get_proxies()
                return proxies, ip_id
            if flag == '0':
                return None, None
        else:
            username = str(experience_ip_dict.get('username'))
            password = str(experience_ip_dict.get('password'))
            ip_id = experience_ip_dict.get('id')
    else:
        username = str(ip_dict.get('username'))
        password = str(ip_dict.get('password'))
        ip_id = ip_dict.get('id')

    proxy = {
        'http': 'socks5h://{}:{}@{}:{}'.format(username, password, settings.PROXY_IP, settings.PROXY_PORT),
        'https': 'socks5h://{}:{}@{}:{}'.format(username, password, settings.PROXY_IP, settings.PROXY_PORT),
    }
    return proxy, ip_id


if __name__ == '__main__':
    # print(get_proxies())
    print(get_my_proxies(39, '0'))
