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
        proxies_accounts = random.sample(PROXY_DICT, 2)

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
        response = requests.post(url, headers=get_header(), json=parser,timeout=10).json()
        # response.raise_for_status()
        if response.get('code') == '000000':
            record_list = response.get('data').get('list')
            break
        else:
            print('binance接口请求失败')
            time.sleep(2)
    # print(record_list)
    return page, record_list

# 爬取分页内容的函数
def fetch_all_pages(uniqueName):
    num_pages = 2
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
            'time': time, # 时间戳
            'symbol': symbol, # 交易对
            'side': side, # 买卖
            'positionSide': position_side, # 持仓方向
            'average_price': average_price, # 开仓平均价格
            'total_quantity': aggregated['quantity'], # 持仓价值USDT（持仓数量*开仓平均价格）
            'total_qty': aggregated['qty'], # 持仓数量
            'total_realizedProfit': aggregated['realizedProfit'] # 持仓收益
        })
    print(result)
    return result


def position_history(uniqueName):
    url = 'https://www.binance.com/bapi/futures/v1/friendly/future/copy-trade/lead-portfolio/position-history'
    parser = {
        'pageNumber': 1,
        'pageSize': 10,
        'portfolioId': uniqueName,
        'sort': 'OPENING'
    }
    while True:
        response = requests.post(url, json=parser, timeout=10).json()
        # response.raise_for_status()
        if response.get('code') == '000000':
            record_list = response.get('data').get('list')
            break
    print(record_list)
    return record_list


def markPrice(symbol):
    url = 'https://fapi.binance.com/fapi/v1/premiumIndex'
    parser = {
        'symbol': symbol
    }
    while True:
        response = requests.get(url, params=parser, timeout=10).json()
        markPrice = float(response.get('markPrice'))
        if markPrice:
            break
    # print(markPrice)
    return markPrice

def blance(uniqueName):
    url = f'https://www.binance.com/bapi/futures/v1/friendly/future/copy-trade/lead-portfolio/detail?portfolioId={uniqueName}'
    res = requests.get(url, timeout=10).json()
    if res.get('code') == '000000':
        marginBlance = float(res.get('data').get('marginBalance'))
    # print(marginBlance)
    return marginBlance



class Spider():
    def __init__(self, uniqueName):
        self.uniqueName = uniqueName
        self.position = []

    def run(self):
        while True:
            old_list = merge_data(self.uniqueName)
            if old_list is None:
                continue
            break
        if old_list[0].get('total_realizedProfit') == 0:
            print(f"交易员{self.uniqueName}有正在进行中的交易, 等待新的交易发生后开始跟随！")
        else:
            print(f"交易员{self.uniqueName}可能尚未开始交易, 等待新的交易发生后开始跟随！")

        while True:
            new_list = merge_data(self.uniqueName)
            if new_list is None:
                continue
            self.analysis(old_list, new_list)
            old_list = new_list
            time.sleep(1)

    def analysis(self, old_list, new_list):
        # 如果old_list和new_list一样，则返回（有持仓则，更新当前持仓）
        if old_list == new_list:
            if self.position:
                """更新持仓数据"""
                for item in self.position:
                    market_price = markPrice(item["symbol"])
                    item['upl_ratio'] = market_price / item['average_price'] - 1  # 币的涨跌，缺杠杆计算得出收益率
                    item['upl'] = (market_price - item['average_price']) * item['total_qty']  # 模拟计算的收益
                    item['posSpace'] = item['total_quantity'] / blance(self.uniqueName)  # 模拟计算的仓位大小
                """再查看是否有hold住的交易符合开仓条件"""
                # todo
            return
        # 查找新增项
        added_items = list(filter(lambda x: x not in old_list, new_list))
        for item in added_items:
            # 开仓、加仓
            if item['total_realizedProfit'] == 0:
                found = False
                for idx, pos_item in enumerate(self.position):
                    if pos_item["symbol"] == item["symbol"] and pos_item["side"] == item["side"]:
                        """更新模拟持仓"""
                        self.position[idx]['total_qty'] += item['total_qty']
                        self.position[idx]['total_quantity'] += item['total_quantity']
                        # market_price = markPrice(pos_item["symbol"])
                        market_price = item['average_price']
                        self.position[idx]['average_price'] = (pos_item["average_price"] + item["average_price"]) / 2
                        self.position[idx]['upl_ratio'] = market_price / self.position[idx]['average_price'] - 1
                        self.position[idx]['upl'] = (market_price - self.position[idx]['average_price']) * self.position[idx][
                            'total_qty']
                        self.position[idx]['posSpace'] = self.position[idx]['total_quantity'] / blance(
                            self.uniqueName)
                        found = True

                        """数据打包"""
                        item['order_type'] = 'open'

                        """判断是否符合要求, 如何符合则开单，不符合则跳过"""

                if not found:
                    self.position.append(item)
                    """数据打包"""
                    item['order_type'] = 'open'

                    """判断是否符合要求, 如何符合则开单，不符合则跳过"""
            # 平仓、减仓
            else:
                for idx, pos_item in enumerate(self.position):
                    # 有持仓，减仓或平仓
                    if pos_item["symbol"] == item["symbol"] and pos_item["side"] != item["side"]:
                        """发送交易信号"""
                        item['order_type'] = 'close'


                        """更新模拟持仓"""
                        self.position[idx]['total_qty'] -= item['total_qty']
                        # 平仓
                        if self.position[idx]['total_qty'] < 0.01:
                            self.position.remove(self.position[idx])
                            #todo 是否可以给closs_all，然后交易脚本将这个币全部平掉
                        # 减仓
                        else:
                            self.position[idx]['total_realizedProfit'] += item['total_realizedProfit']
                            self.position[idx]['total_quantity'] -= item['total_quantity']
                            market_price = item["average_price"]
                            self.position[idx]['upl_ratio'] = market_price / pos_item['average_price'] - 1
                            self.position[idx]['upl'] = (market_price - pos_item['average_price']) * \
                                                        self.position[idx]['total_qty']
                            self.position[idx]['posSpace'] = self.position[idx]['total_quantity'] / blance(
                                self.uniqueName)








if __name__ == '__main__':
    # fetch_all_pages('3968633605600864001')

    # start = time.time()
    merge_data('3956629888625639169')
    # position('3901846209383087104')
    # Spider('4025553485863672065').run()

    # while True:
    #     markPrice('ALTUSDT')

    # end = time.time()
    # print(end - start)

    # proxy_list = get_proxies_list()
    # print(proxy_list)
    #
    # proxy = {'http': 'socks5h://15755149931sct-36:8ivtkleb@154.9.255.134:5002',
    #         'https': 'socks5h://15755149931sct-36:8ivtkleb@154.9.255.134:5002'}
    # # fetch_page('3968633605600864001', 1, proxy)

    # position_history(4025553485863672065)
