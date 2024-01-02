from crawler.utils.db import Connect
from crawler import settingsdev as settings
import random


# 随机获取所有用户的代理，用于爬虫
def get_proxies():
    with Connect() as conn:
        PROXY_DICT = conn.fetch_all("select username,password from api_ipinfo where countdown>0")

    proxies_account = random.choice(PROXY_DICT)

    proxies = {
        'http': 'socks5h://{}:{}@{}:{}'.format(proxies_account['username'], proxies_account['password'],
                                               settings.PROXY_IP,
                                               settings.PROXY_PORT),
        'https': 'socks5h://{}:{}@{}:{}'.format(proxies_account['username'], proxies_account['password'],
                                                settings.PROXY_IP,
                                                settings.PROXY_PORT),
        # 'all': 'socks5h://15755149931sct-5:8ivtkleb@38.147.173.111:5003'
    }
    return proxies


# 获取用户自己的代理，用于交易
def get_my_proxies(user_id, flag):
    with Connect() as conn:
        ip_dict = conn.fetch_one(
            "select username,password from api_ipinfo where user_id=%(user_id)s AND countdown>0",
            user_id={user_id})

        # 如果用户用模拟盘测试，但没有提供固定ip，则随机选择一个ip给用户使用
        if ip_dict is None and flag == '1':
            # ip_dict = conn.fetch_one(
            #     "select username,password from api_ipinfo where countdown>0")
            proxies = get_proxies()
            return proxies

        if ip_dict is None and flag == '0':
            return None

        username = str(ip_dict.get('username'))
        password = str(ip_dict.get('password'))
        proxy = {
            'http': 'socks5h://{}:{}@{}:{}'.format(username, password, settings.PROXY_IP, settings.PROXY_PORT),
            'https': 'socks5h://{}:{}@{}:{}'.format(username, password, settings.PROXY_IP, settings.PROXY_PORT),
        }
    return proxy


if __name__ == '__main__':
    # print(get_proxies())
    print(get_my_proxies(2, '0'))
