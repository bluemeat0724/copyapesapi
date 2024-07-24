import requests
import time


def spider(uniqueName):
    url = f'https://www.binance.com/bapi/futures/v1/friendly/future/copy-trade/lead-data/positions?portfolioId={uniqueName}'
    # proxies = proxy
    while True:
        response = requests.get(url, timeout=10).json()
        # print(response)
        if response.get('code') == '000000':
            list = response.get('data')
            break
        else:
            print('binance接口请求失败')
            time.sleep(2)
    positions = []
    for i in list:
        if float(i.get('positionAmount')) != 0:
            symbol = i.get('symbol')  # 交易对
            positionAmount = float(i.get('positionAmount'))  # 持仓量 小于0表示开空 大于0表示开多
            notionalValue = float(i.get('notionalValue'))  # 持仓价值 持仓量*当前市价
            entryPrice = float(i.get('entryPrice')) # 开仓价
            leverage = float(i.get('leverage'))  # 杠杆

            positionSide = i.get('positionSide')  # 持仓方向
            if positionSide == 'BOTH':
                if positionAmount > 0:
                    positionSide = 'LONG'
                else:
                    positionSide = 'SHORT'

            unrealizedProfit = float(i.get('unrealizedProfit'))  # 未实现盈亏
            isolated = i.get('isolated')  # 是否是逐仓
            margin = notionalValue / leverage  # 持仓保证金
            upl_ratio = unrealizedProfit / abs(margin) # 未实现收益率
            marginBlance = blance(uniqueName)
            posSpace = abs(notionalValue) / marginBlance

            data_clear = {
                'symbol': symbol,  # 交易对
                'positionAmount': positionAmount, # 持仓量 小于0表示开空 大于0表示开多
                'notionalValue': notionalValue, # 持仓价值 持仓量*当前市价
                'entryPrice': entryPrice, # 开仓价
                'leverage': leverage, # 杠杆
                'positionSide': positionSide, # 持仓方向
                'unrealizedProfit': unrealizedProfit, # 未实现盈亏
                'isolated': isolated, # 是否是逐仓
                'margin': margin, # 持仓保证金
                'upl_ratio': upl_ratio, # 未实现收益率
                'posSpace': posSpace,
            }
            positions.append(data_clear)
    print(positions)
    return positions

def blance(uniqueName):
    url = f'https://www.binance.com/bapi/futures/v1/friendly/future/copy-trade/lead-portfolio/detail?portfolioId={uniqueName}'
    res = requests.get(url, timeout=10).json()
    if res.get('code') == '000000':
        marginBlance = float(res.get('data').get('marginBalance'))
    print(marginBlance)
    return marginBlance

def analysis(old_list, new_list):
    # 如果没有交易数据，则直接返回
    if not new_list and not old_list:
        return None
    old_set = set((i['symbol'], i['isolated'], i['positionSide']) for i in old_list)
    added_items = list(filter(lambda x: (x['symbol'], x['isolated'], x['positionSide']) not in old_set, new_list))
    if added_items:
        for item in added_items:
            item['order_type'] = 'open'
            '''封装交易信息,推送redis'''
            print(item)

    # 查找减少的交易数据
    removed_items = [i for i in old_list if
                     (i['symbol'], i['isolated'], i['positionSide']) not in set(
                         map(lambda x: (x['symbol'], x['isolated'], x['positionSide']), new_list))]
    if removed_items:
        for item in removed_items:
            item['order_type'] = 'close'
            '''封装交易信息,推送redis'''
            print(item)

    # 查找值变化的数据
    for old_item, new_item in zip(old_list, new_list):
        if old_item["symbol"] == new_item["symbol"] and old_item["isolated"] == new_item["isolated"] and old_item[
            'positionSide'] == new_item['positionSide'] and old_item[
            'positionAmount'] != new_item['positionAmount']:  # todo 如果是用保证金去开仓就用margin替代positionAmount
            change = {
                'order_type': 'change',
                'symbol': new_item['symbol'],
                'new_positionAmount': new_item['positionAmount'],
                'old_positionAmount': old_item['positionAmount'],
                'leverage': new_item['leverage'],
                'positionSide': new_item['positionSide'],
                'upl_ratio': new_item['upl_ratio'],
                'margin': new_item['margin'],
                'isolated': new_item['isolated'],
            }
            print(change)



def run(uniqueName):
    while True:
        old_list = spider(uniqueName)
        if old_list is None:
            continue
        break
    if old_list:
        print(f"交易员{uniqueName}有正在进行中的交易, 等待新的交易发生后开始跟随！")
    else:
        print(f"交易员{uniqueName}尚未开始交易, 等待新的交易发生后开始跟随！")

    while True:
        new_list = spider(uniqueName)
        if new_list is None:
            continue
        analysis(old_list, new_list)
        old_list = new_list
        time.sleep(1)



if __name__ == '__main__':
    spider('4025553485863672065')
    # blance('4025553485863672065')
    # run('4025553485863672065')
    # while True:
    #     spider('4025553485863672065')