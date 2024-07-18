import requests
import time
from datetime import datetime
from crawler.utils.get_proxies import get_proxies
from crawler.utils.get_header import get_header
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from crawler.utils.db import Connect
from crawler import settingsdev as settings
import random
from itertools import cycle

def get_proxies_list():
    with Connect() as conn:
        PROXY_DICT = conn.fetch_all("select username,password,id from api_ipinfo where countdown>0 AND experience_day=0")
        # print(PROXY_DICT)

        # 随机选择三个代理IP账号
        proxies_accounts = random.sample(PROXY_DICT, 3)

        proxies_list = []
        for proxies_account in proxies_accounts:
            proxies = {
                'http': 'socks5h://{}:{}@{}:{}'.format(proxies_account['username'], proxies_account['password'],
                                                       settings.PROXY_IP,
                                                       settings.PROXY_PORT),
                'https': 'socks5h://{}:{}@{}:{}'.format(proxies_account['username'], proxies_account['password'],
                                                        settings.PROXY_IP,
                                                        settings.PROXY_PORT)
            }
            proxies_list.append(proxies)

        return proxies_list

def fetch_page(uniqueName, page, proxy):
    url = 'https://www.binance.com/bapi/futures/v1/friendly/future/copy-trade/lead-portfolio/trade-history'
    parser = {
        'pageNumber': page,
        'pageSize': 50,
        'portfolioId': uniqueName
              }
    proxies = proxy
    while True:
        response = requests.post(url, headers=get_header(), json=parser, proxies=proxies,timeout=10).json()
        # response.raise_for_status()
        if response.get('code') == '000000':
            record_list = response.get('data').get('list')
            break
        else:
            time.sleep(2)
    print(record_list)
    return page, record_list

# 爬取分页内容的函数
def fetch_all_pages(uniqueName):
    num_pages = 3
    results = {}
    proxies_list = get_proxies_list()
    proxy_cycle = cycle(proxies_list)  # 创建一个循环迭代器
    with ThreadPoolExecutor(max_workers=len(proxies_list)) as executor:
        future_to_page = {executor.submit(fetch_page, uniqueName, page, next(proxy_cycle)): page for page in
                          range(1, num_pages + 1)}
        for future in as_completed(future_to_page):
            page, record_list = future.result()
            if record_list is not None:
                results[page] = record_list

    # 按分页顺序返回结果并合并所有分页内容
    ordered_results = [results[page] for page in sorted(results.keys()) if page in results]
    merged_results = [item for sublist in ordered_results for item in sublist]
    # print(merged_results,len(merged_results))
    return merged_results

def merge_data(uniqueName):
    record_list = fetch_all_pages(uniqueName)
    # 初始化用于聚合数据的字典
    aggregated_data = defaultdict(lambda: {'quantity': 0, 'qty': 0, 'total_price_x_quantity': 0, 'realizedProfit': 0.0})

    # 聚合数据
    for entry in record_list:
        key = (entry['time'], entry['symbol'], entry['side'], entry['positionSide'])
        aggregated_data[key]['quantity'] += entry['quantity']
        aggregated_data[key]['qty'] += entry['qty']
        aggregated_data[key]['total_price_x_quantity'] += entry['price'] * entry['quantity']
        aggregated_data[key]['realizedProfit'] += entry['realizedProfit']

    # 计算平均价格并构造结果列表
    result = []
    for (time, symbol, side, position_side), aggregated in aggregated_data.items():
        average_price = aggregated['total_price_x_quantity'] / aggregated['quantity'] if aggregated['quantity'] else 0
        result.append({
            'time': time,
            'symbol': symbol,
            'side': side,
            'positionSide': position_side,
            'average_price': average_price,
            'total_quantity': aggregated['quantity'],
            'total_qty': aggregated['qty'],
            'total_realizedProfit': aggregated['realizedProfit']
        })
    print(result)
    return result



if __name__ == '__main__':
    # fetch_all_pages('3968633605600864001')
    # merge_data('3887627985594221568')

    # proxy_list = get_proxies_list()
    # print(proxy_list)

    proxy = {'http': 'socks5h://15755149931sct-36:8ivtkleb@154.9.255.134:5002',
            'https': 'socks5h://15755149931sct-36:8ivtkleb@154.9.255.134:5002'}
    fetch_page('3968633605600864001', 1, proxy)