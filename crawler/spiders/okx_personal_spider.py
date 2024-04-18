import requests
import time
from datetime import datetime, timedelta, timezone
from crawler.utils.get_header import get_header
from crawler.utils.get_proxies import get_proxies
import json


now = int(time.time()) * 1000

# 获取当前日期和时间
_now = datetime.now(timezone.utc)

# 获取昨天的日期，时间设为15:59:59
thirty_days_ago_specific_time = (_now - timedelta(days=30)).replace(hour=16, minute=0, second=0, microsecond=0)
thirty_days_ago_specific_time_timestamp = int(thirty_days_ago_specific_time.timestamp()) * 1000

# Get today's date at 16:00:00
today_specific_time = (_now + timedelta(days=2)).replace(hour=16, minute=0, second=0, microsecond=0)
today_specific_time_timestamp = int(today_specific_time.timestamp()) * 1000


def spider(uniqueName):
    summary_list_new = []
    try:
        position_url = f'https://www.okx.com/priapi/v5/ecotrade/public/positions-v2?limit=10&uniqueName={uniqueName}&t={now}'
        position_list = requests.get(position_url, headers=get_header(), proxies=get_proxies()[0], timeout=30).json().get('data', list())[0].get('posData', list())
        # test_record_url = f'https://www.okx.com/priapi/v5/ecotrade/public/trade-records?limit=5&startModify={thirty_days_ago_specific_time_timestamp}&endModify={today_specific_time_timestamp}&uniqueName={uniqueName}&t={now}'
        # test_record_list = requests.get(test_record_url, headers=get_header(), timeout=30).json().get('data', list())
        # # 将记录列表写入文本文件
        # with open(f'test_record_list_{uniqueName}.txt', 'a') as file:
        #     # 使用json.dumps将列表转换为字符串格式，便于阅读
        #     file.write(f'{datetime.now()}\n')
        #     file.write(json.dumps(test_record_list, indent=4))
        if not position_list:
            return summary_list_new
        record_url = f'https://www.okx.com/priapi/v5/ecotrade/public/trade-records?limit=10&startModify={thirty_days_ago_specific_time_timestamp}&endModify={today_specific_time_timestamp}&uniqueName={uniqueName}&t={now}'
        # print(record_url)
        record_list = requests.get(record_url, headers=get_header(), timeout=30).json().get('data', list())
        # print(record_list)
        for record in record_list:
            posSide = record.get('posSide')
            side = record.get('side')
            data_clear = {
                'instId': record.get('instId'),
                'openTime': record.get('cTime'),  # 用于判断是否是最新的交易记录
                'posSide': posSide,
                'lever': record.get('lever'),
                'openAvgPx': record.get('avgPx'),  # 冗余字段
            }

            exist = False
            for item in position_list:
                if item.get('instId') == data_clear['instId'] and item.get('posSide') == data_clear['posSide']:
                    data_clear['mgnMode'] = item.get('mgnMode')
                    pos = int(item.get('pos'))
                    exist = True
                    '''
                    持仓方向
                    买卖模式下：可不填写此参数，默认值net，如果填写，仅可以填写net
                    开平仓模式下： 必须填写此参数，且仅可以填写 long：平多 ，short：平空
                    
                    买卖模式下：交割/永续/期权：pos为正代表开多，pos为负代表开空
                    
                    开平仓模式下，side和posSide需要进行组合
                    开多：买入开多（side 填写 buy； posSide 填写 long ）
                    开空：卖出开空（side 填写 sell； posSide 填写 short ）
                    平多：卖出平多（side 填写 sell；posSide 填写 long ）
                    平空：买入平空（side 填写 buy； posSide 填写 short ）
                    '''
                    if data_clear['posSide'] != 'net':
                        if side == 'buy':
                            if data_clear['posSide'] == 'long':
                                data_clear['order_type'] = 'open'
                            else:
                                data_clear['order_type'] = 'reduce'
                        else:
                            if data_clear['posSide'] == 'short':
                                data_clear['order_type'] = 'open'
                            else:
                                data_clear['order_type'] = 'reduce'  # 减仓
                    elif data_clear['posSide'] == 'net':
                        if side == 'buy' and int(pos) > 0: # 买入开多
                            data_clear['order_type'] = 'open'
                            data_clear['posSide'] = 'long'
                        elif side == 'sell' and pos < 0: # 卖出开空
                            data_clear['order_type'] = 'open'
                            data_clear['posSide'] = 'short'
                        elif side == 'buy' and pos < 0: # 买入平空
                            data_clear['order_type'] = 'reduce'
                            data_clear['posSide']= 'short'
                        elif side == 'sell' and pos > 0: # 卖出平多
                            data_clear['order_type'] = 'reduce'
                            data_clear['posSide'] = 'long'

            if not exist:
                data_clear['order_type'] = 'close'  # 平仓
                if posSide == 'net':
                    if side == 'buy':
                        data_clear['posSide'] = 'short'
                    elif side == 'sell':
                        data_clear['posSide'] = 'long'
            summary_list_new.append(data_clear)
        return summary_list_new
    except Exception as e:
        # print('personal_spider',datetime.now())
        # print(e)
        pass

def spider_close_item(uniqueName):
    summary_list_new = []
    attempts = 0
    max_attempts = 10
    while attempts < max_attempts:
        try:
            record_url = f'https://www.okx.com/priapi/v5/ecotrade/public/trade-records?limit=1&startModify={thirty_days_ago_specific_time_timestamp}&endModify={today_specific_time_timestamp}&uniqueName={uniqueName}&t={now}'
            # print(record_url)
            record_list = requests.get(record_url, headers=get_header(), timeout=30).json().get('data', list())
            print(record_list)

            posSide = record_list[0].get('posSide')
            side = record_list[0].get('side')
            if posSide == 'net':
                if side == 'buy':
                    posSide = 'short'
                elif side == 'sell':
                    posSide = 'long'

            data_clear = {
                'instId': record_list[0].get('instId'),
                'openTime': record_list[0].get('cTime'),
                'posSide': posSide,
                'lever': record_list[0].get('lever'),
                'openAvgPx': record_list[0].get('avgPx'),
                'order_type': 'close'
            }
            summary_list_new.append(data_clear)
            return summary_list_new
        except Exception as e:
            time.sleep(1)
            # print('spider_close', datetime.now())
            # print(e)
        finally:
            attempts += 1
    return summary_list_new

if __name__ == '__main__':
    print(spider('A8AF8AFFAB6051B3'))
    # print(spider_close_item('032805718789399F'))
