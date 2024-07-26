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

# def test(uniqueName, page):
#     url = 'https://www.binance.com/bapi/futures/v1/friendly/future/copy-trade/lead-portfolio/trade-history'
#     parser = {
#         'pageNumber': page,
#         'pageSize': 50,
#         'portfolioId': uniqueName
#     }
#     while True:
#         response = requests.post(url, json=parser, timeout=10).json()
#         # response.raise_for_status()
#         if response.get('code') == '000000':
#             record_list = response.get('data').get('list')
#             break
#         else:
#             print('binance接口请求失败')
#             time.sleep(2)
#     print(record_list)
#     return page, record_list

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



def position(uniqueName):
    pos = []
    # record_list = merge_data(uniqueName)
    record_list = fetch_all_pages(uniqueName)

    if record_list and record_list[0].get('realizedProfit') == 0:
        # 如果第一个元素的 total_realizedProfit 是 0
        for item in record_list:
            if item.get('realizedProfit') == 0:
                pos.append(item)
            else:
                break
    else:
        for item in record_list:
            if item.get('realizedProfit') != 0:
                pos.append(item)
            else:
                break
    # else:
    #     # 第一个元素的 total_realizedProfit 不为 0 或者列表为空
    #     found_non_zero = False
    #     for item in record_list:
    #         if not found_non_zero:
    #             # 添加持仓收益不为 0 的数据到 pos 列表中
    #             if item.get('total_realizedProfit') != 0:
    #                 pos.append(item)
    #             else:
    #                 found_non_zero = True
    #                 pos.append(item)
            # else:
            #     # 添加持仓收益为 0 的数据到 pos 列表中，直到遇到下一个非 0 的数据
            #     if item.get('total_realizedProfit') == 0:
            #         pos.append(item)
            #     else:
            #         break
    print(pos)
    if not pos:
        print('没有持仓')
        return pos

    # 聚合数据
    aggregated_data = defaultdict(lambda: {'quantity': 0, 'qty': 0,'total_price_x_quantity': 0, 'realizedProfit': 0.0})
    for entry in pos:  # 这里改为遍历 pos 列表
        key = (entry['symbol'], entry['side'], entry['positionSide'])
        aggregated_data[key]['quantity'] += entry['quantity']
        aggregated_data[key]['qty'] += entry['qty']
        aggregated_data[key]['total_price_x_quantity'] += entry['price'] * entry['quantity']
        aggregated_data[key]['realizedProfit'] += entry['realizedProfit']

    # 计算平均价格并构造结果列表
    result = []
    for (symbol, side, position_side), aggregated in aggregated_data.items():
        average_price = aggregated['total_price_x_quantity'] / aggregated['quantity'] if aggregated[
            'quantity'] else 0
        market_price = markPrice(symbol)
        upl_ratio = market_price / average_price - 1
        total_qty = aggregated['qty']
        upl = (market_price - average_price) * total_qty
        marginBlance = blance(uniqueName)
        total_quantity = aggregated['quantity']
        posSpace = total_quantity / marginBlance
        if side == 'SELL':
            upl = -upl
            upl_ratio = -upl_ratio

        result.append({
            'symbol': symbol,  # 交易对
            'side': side,  # 买卖
            'positionSide': position_side,  # 持仓方向
            'average_price': average_price,  # 开仓平均价格
            'total_quantity': total_quantity,
            'total_qty': total_qty,  # 持仓数量
            'total_realizedProfit': aggregated['realizedProfit'],  # 持仓收益
            'upl_ratio': upl_ratio,  # 币价格涨幅，不是交易员的收益率，缺少交易员杠杆
            'upl': upl, # 未实现持仓收益
            'posSpace': posSpace,  # 仓位比例
        })

    print(result)
    return result

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
        self.average_price_dic = {}

    def run(self):
        while True:
            # old_list = position(self.uniqueName)
            old_list = position(self.uniqueName)
            if old_list is None:
                continue
            break
        if old_list[0].get('total_realizedProfit') == 0:
            print(f"交易员{self.uniqueName}有正在进行中的交易, 等待新的交易发生后开始跟随！")
        else:
            print(f"交易员{self.uniqueName}可能尚未开始交易, 等待新的交易发生后开始跟随！")

        while True:
            new_list = position(self.uniqueName)
            if new_list is None:
                continue
            # self.analysis(old_list, new_list)
            self.analysis_1(old_list, new_list)
            old_list = new_list
            time.sleep(1)

    def analysis(self, old_list, new_list):
        for old_item, new_item in zip(old_list, new_list):
            # 新旧数据无变化，更新持仓后直接返回，如没有则添加，此处只做模拟仓位更新，不做交易推送
            # 判断：realizedProfit为0（开仓加仓记录）
            if old_item["symbol"] == new_item["symbol"] and old_item["side"] == new_item["side"] and old_item[
                'total_qty'] == new_item['total_qty'] and old_item[
                'total_realizedProfit'] == new_item['total_realizedProfit'] == 0:
                found = False
                for idx, pos_item in enumerate(self.position):
                    # 判断：symbol、side、total_qty相同，相同说明new_list是单一币种连续加仓，最后一次加仓后的记录，直接覆盖更新数据
                    if pos_item["symbol"] == new_item["symbol"] and pos_item["side"] == new_item["side"]:
                    # if pos_item["symbol"] == new_item["symbol"] and pos_item["side"] == new_item["side"] and pos_item['total_qty'] == new_item['total_qty']:
                        self.position[idx] = new_item  # 更新现有条目
                        return
                    # 判断：symbol、side、total_qty不相同，不相同说明new_list是单一币种没有连续加仓，中间有其他币种操作，手动更新仓位数据，不直接覆盖
                    # else:
                    #     if self.average_price_dic.get(f'{pos_item["symbol"]}-{pos_item["side"]}', 0) == pos_item["average_price"]:
                    #         return
                        # pos_item["average_price"] = (pos_item["average_price"] + new_item["average_price"])/2
                        # # 将更新后的持仓平均开仓价格存入average_price_dic
                        # self.average_price_dic[f'{pos_item["symbol"]}-{pos_item["side"]}'] = pos_item["average_price"]
                        #
                        # market_price = markPrice(pos_item["symbol"])
                        # self.position[idx]['upl_ratio'] = market_price / pos_item["average_price"] - 1
                        # self.position[idx]['upl'] = (market_price - pos_item["average_price"]) * self.position[idx][
                        #     'total_qty']
                        # self.position[idx]['posSpace'] = self.position[idx]['total_quantity'] / blance(self.uniqueName)

                if not found:
                    self.position.append(new_item)  # 添加新条目
                    return
            # # 判断：realizedProfit不为0（减仓平仓记录）
            # elif old_item["symbol"] == new_item["symbol"] and old_item["side"] == new_item["side"] and old_item[
            #     'total_qty'] == new_item['total_qty'] and old_item[
            #     'total_realizedProfit'] == new_item['total_realizedProfit'] != 0:
            #     return

            # 新旧数据有变化，更新持仓
            # 加仓（单一币种连续加仓，中间没有掺杂其他币种操作）
            if old_item["symbol"] == new_item["symbol"] and old_item["side"] == new_item["side"] and old_item[
                'total_qty'] != new_item['total_qty'] and old_item[
                'total_realizedProfit'] == new_item['total_realizedProfit'] == 0:
                for idx, pos_item in enumerate(self.position):
                    if pos_item["symbol"] == new_item["symbol"] and pos_item["side"] == new_item["side"]:
                        self.position[idx] = new_item  # 更新现有条目
                        # 加仓量
                        sum = new_item['total_qty'] - pos_item['total_qty']

                        # market_price = markPrice(pos_item["symbol"])
                        # self.position[idx]['upl_ratio'] = market_price / pos_item["average_price"] - 1
                        # self.position[idx]['upl'] = (market_price - pos_item["average_price"]) * self.position[idx][
                        #     'total_qty']
                        # self.position[idx]['posSpace'] = self.position[idx]['total_quantity'] / blance(self.uniqueName)
                        print(f"交易员{self.uniqueName}加仓了{pos_item['symbol']}{sum}")
                        return
            # 新旧数据有变化，更新持仓
            # 减仓平仓（单一币种连续减仓，中间没有掺杂其他币种操作）
            elif old_item["symbol"] == new_item["symbol"] and old_item["side"] == new_item["side"] and old_item[
                'total_qty'] != new_item['total_qty'] and old_item[
                'total_realizedProfit'] == new_item['total_realizedProfit'] != 0:
                # 查看当前是否有模拟持仓记录
                for idx, pos_item in enumerate(self.position):
                    if pos_item["symbol"] == new_item["symbol"] and pos_item["side"] != new_item["side"]:
                        self.position[idx]['total_qty'] -= new_item['total_qty']
                        if self.position[idx]['total_qty'] < 0.01:  # 考虑到精度问题，移仓数量小于 0.01 则移除，平仓
                            self.position.remove(self.position[idx])
                            print(f"交易员{self.uniqueName}平仓了{pos_item['symbol']}")
                            return
                        self.position[idx]['total_realizedProfit'] = new_item['total_realizedProfit']
                        self.position[idx]['total_quantity'] -= new_item['total_quantity']

                        market_price = new_item["average_price"]
                        self.position[idx]['upl_ratio'] = market_price / pos_item["average_price"] - 1
                        self.position[idx]['upl'] = (market_price - pos_item["average_price"]) * self.position[idx][
                            'total_qty']
                        self.position[idx]['posSpace'] = self.position[idx]['total_quantity'] / blance(self.uniqueName)
                        # 减仓量
                        sum = pos_item['total_qty'] - new_item['total_qty']
                        print(f"交易员{self.uniqueName}减仓了{pos_item['symbol']}{sum}")
                        return


        # 新增交易记录，判断加仓减仓
        old_set = set((i['symbol'], i['side'], i['total_realizedProfit']) for i in old_list)
        added_items = list(filter(lambda x: (x['symbol'], x['side'], x['total_realizedProfit']) not in old_set, new_list))
        # 新开或加仓
        if added_items and new_list[0]['total_realizedProfit'] == 0:
            found = False
            for idx, pos_item in enumerate(self.position):
                # 加仓
                if pos_item["symbol"] == new_item["symbol"] and pos_item["side"] == new_item["side"]:
                    self.position[idx]['total_qty'] += new_item['total_qty']
                    self.position[idx]['total_quantity'] += new_item['total_quantity']

                    market_price = markPrice(pos_item["symbol"])
                    self.position[idx]['upl_ratio'] = market_price / pos_item["average_price"] - 1
                    self.position[idx]['upl'] = (market_price - pos_item["average_price"]) * self.position[idx]['total_qty']
                    self.position[idx]['posSpace'] = self.position[idx]['total_quantity'] / blance(self.uniqueName)
                    print(f"交易员{self.uniqueName}减仓了{pos_item['symbol']}")
                    return
            if not found:
                self.position.append(new_item)  # 添加新条目
                return
        # 平仓或者减仓
        elif added_items and new_list[0]['total_realizedProfit'] != 0:
            found = False
            for idx, pos_item in enumerate(self.position):
                if pos_item["symbol"] == new_item["symbol"] and pos_item["side"] == new_item["side"]:
                    self.position[idx]['total_qty'] -= new_item['total_qty']
                    if self.position[idx]['total_qty'] < 0.01:  # 考虑到精度问题，移仓数量小于 0.01 则移除，平仓
                        self.position.remove(self.position[idx])
                        print(f"交易员{self.uniqueName}平仓了{pos_item['symbol']}")
                        return
                    self.position[idx]['total_realizedProfit'] = new_item['total_realizedProfit']
                    self.position[idx]['total_quantity'] -= new_item['total_quantity']

                    market_price = new_item["average_price"]
                    self.position[idx]['upl_ratio'] = market_price / pos_item["average_price"] - 1
                    self.position[idx]['upl'] = (market_price - pos_item["average_price"]) * self.position[idx]['total_qty']
                    marginBlance = blance(self.uniqueName)
                    self.position[idx]['posSpace'] = self.position[idx]['total_quantity'] / marginBlance
                    print(f"交易员{self.uniqueName}减仓了{pos_item['symbol']}")
                    return
            if not found:
                print(f"没有找到持仓信息{pos_item['symbol']}")
                return

    def analysis_1(self, old_list, new_list):
        # 如果old_list和new_list一样，则返回（有持仓则，更新当前持仓）
        if old_list == new_list:
            if self.position:
                """更新持仓数据"""
                for item in self.position:
                    market_price = markPrice(item["symbol"])
                    item['upl_ratio'] = market_price / item['average_price'] - 1
                    item['upl'] = (market_price - item['average_price']) * item['total_qty']
                    item['posSpace'] = item['total_quantity'] / blance(self.uniqueName)
                """再查看是否有hold住的交易符合开仓条件"""
            return
        # 查找新增项
        added_items = list(filter(lambda x: x not in old_list, new_list))
        if not added_items:
            return
        for item in added_items:
            # 开仓、加仓
            if item['total_realizedProfit'] == 0:
                found = False
                for idx, pos_item in enumerate(self.position):
                    if pos_item["symbol"] == item["symbol"] and pos_item["side"] == item["side"]:
                        """更新模拟持仓"""
                        self.position[idx]['total_qty'] += item['total_qty']
                        self.position[idx]['total_quantity'] += item['total_quantity']
                        market_price = markPrice(pos_item["symbol"])
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
                found = False
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
                            found = True
                if not found:
                    return







if __name__ == '__main__':
    # fetch_all_pages('3968633605600864001')

    # start = time.time()
    merge_data('3901846209383087104')
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
