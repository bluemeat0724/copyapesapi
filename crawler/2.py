from crawler.utils.db import Connect
import settings
import random
from okx.api._client import ResponseStatusError

# ids = 2
#
# with Connect() as conn:
#     ip_dict = conn.fetch_one("select username,password from api_ipinfo where user_id=%(user_id)s AND countdown>0",  user_id={ids})
#     print(ip_dict)
#     username = str(ip_dict.get('username'))
#     password = str(ip_dict.get('password'))
#     proxy = {
#         'http': 'socks5h://{}:{}@{}:{}'.format(username, password, settings.PROXY_IP, settings.PROXY_PORT),
#         'https': 'socks5h://{}:{}@{}:{}'.format(username, password, settings.PROXY_IP, settings.PROXY_PORT),
#     }
#
# print(proxy)


# with Connect() as conn:
#     # api_dict = conn.fetch_one("select username,password from api_ipinfo where user_id=%(user_id)s AND countdown>0", user_id={ids})
#     ip_dict = conn.fetch_one(
#         "select username,password from api_ipinfo where countdown>0")
#     print(ip_dict)


# with Connect() as conn:
#     PROXY_DICT = conn.fetch_all("select username,password from api_ipinfo where countdown>0")
#
# proxies_account = random.choice(PROXY_DICT)
#
# proxies = {
#     'http': 'socks5h://{}:{}@{}:{}'.format(proxies_account['username'], proxies_account['password'],
#                                            settings.PROXY_IP,
#                                            settings.PROXY_PORT),
#     'https': 'socks5h://{}:{}@{}:{}'.format(proxies_account['username'], proxies_account['password'],
#                                             settings.PROXY_IP,
#                                             settings.PROXY_PORT),
#     # 'https': 'socks5h://15755149931sct-5:8ivtkleb@38.147.173.111:5003'
#     # 'all': 'socks5h://15755149931sct-5:8ivtkleb@38.147.173.111:5003'
# }
# print(proxies)

# def log_to_dict(log_file_path):
#     log_dict_list = []
#     with open(log_file_path, 'r', encoding='utf-8') as file:
#         for line in file:
#             parts = line.strip().split(" | ")
#             date, color, description = parts[0], parts[1], parts[2]
#             # 分割标题和描述
#             if '，' in description:
#                 title, desc = description.split('，', 1)
#             else:
#                 title, desc = description, ''
#             log_dict_list.append({
#                 'title': title,
#                 'date': date,
#                 'description': desc,
#                 'color': color
#             })


from datetime import datetime, timedelta, timezone

# Converting another provided timestamp (in milliseconds) to datetime
new_timestamp_3 = 1714273934090 / 1000  # converting milliseconds to seconds
new_date_time_3 = datetime.fromtimestamp(new_timestamp_3, tz=timezone.utc)

print(new_date_time_3.strftime("%Y-%m-%d %H:%M:%S %Z"))

# from datetime import datetime
# import pytz
#
# # 定义东八区时区
# eastern_eight_zone = pytz.timezone('Asia/Shanghai')
#
# # 获取当前日期在东八区的时间
# now_eastern = datetime.now(eastern_eight_zone)
#
# # 设置时间为今天的14:00:00，东八区时区
# specific_time_eastern = now_eastern.replace(hour=16, minute=0, second=0, microsecond=0)
#
# # 将东八区时间转换为UTC时间
# specific_time_utc = specific_time_eastern.astimezone(pytz.utc)
#
# # 获取UTC时间的时间戳，并转换为整数（秒）
# specific_timestamp_utc = int(specific_time_utc.timestamp())
#
# print(specific_timestamp_utc)

# a = [{'instId': 'DOGE-USDT-SWAP', 'openTime': '1713115983581', 'posSide': 'long', 'lever': '10.0', 'openAvgPx': '0.15118', 'order_type': 'close'}]
# if not a:
#     print('1')


import socket

def get_local_ip():
    try:
        # 创建一个socket对象
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 使用Google的公共DNS服务器地址来获取socket的连接
        s.connect(("8.8.8.8", 80))
        # 获取本地接口的IP地址
        ip = s.getsockname()[0]
    finally:
        # 关闭socket连接
        s.close()
    return ip

# 调用函数并打印本地IP地址
print(get_local_ip())
