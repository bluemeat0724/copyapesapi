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
