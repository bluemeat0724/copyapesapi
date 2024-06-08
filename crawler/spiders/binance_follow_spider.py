import requests
import time
from datetime import datetime
from crawler.utils.get_proxies import get_proxies
from crawler.utils.get_header import get_header
from collections import defaultdict



def spider(uniqueName):
    url = 'https://www.binance.com/bapi/futures/v1/friendly/future/copy-trade/lead-portfolio/trade-history'
    parser = {
        'pageNumber': 1,
        'pageSize': 50,
        'portfolioId': uniqueName
              }
    record_list = requests.post(url, headers=get_header(), json=parser).json().get('data').get('list')
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
    return result



if __name__ == '__main__':
    print(spider('3968633605600864001'))
>>>>>>> develop
