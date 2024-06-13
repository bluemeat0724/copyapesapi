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
        position_list = requests.get(position_url, headers=get_header(), timeout=30).json().get('data', list())[0].get(
            'posData', list())
        if not position_list:
            return summary_list_new

        for item in position_list:
            data_clear = {
                'instId': item.get('instId'),
                'openTime': item.get('cTime'),  # 用于判断是否是最新的交易记录
                'posSide': item.get('posSide'),
                'lever': item.get('lever'),
                'pos': item.get('pos'),
                'openAvgPx': item.get('avgPx'),  # 冗余字段
                'mgnMode': item.get('mgnMode'),
                'posSpace':float(item.get('posSpace'))
            }
            pos = int(item.get('pos'))
            if data_clear['posSide'] == 'net':
                if pos > 0:
                    data_clear['posSide'] = 'long'
                elif pos < 0:
                    data_clear['posSide'] = 'short'
            summary_list_new.append(data_clear)
        return summary_list_new
    except Exception as e:
        print('personal_spider',datetime.now())
        print(e)
        pass


def spider_close_item(uniqueName):
    summary_list_new = []
    attempts = 0
    max_attempts = 10
    while attempts < max_attempts:
        try:
            record_url = f'https://www.okx.com/priapi/v5/ecotrade/public/trade-records?limit=1&startModify={thirty_days_ago_specific_time_timestamp}&endModify={today_specific_time_timestamp}&uniqueName={uniqueName}&t={now}'
            # print(record_url)
            record_list = requests.get(record_url, headers=get_header(),proxies=get_proxies()[0], timeout=30).json().get('data', list())
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


def get_position(uniqueName):
    set_flg = True
    while set_flg:
        try:
            position_url = f'https://www.okx.com/priapi/v5/ecotrade/public/positions-v2?limit=10&uniqueName={uniqueName}&t={now}'
            position_list = requests.get(position_url, headers=get_header(),proxies=get_proxies()[0], timeout=30).json().get('data', list())[
                0].get('posData', list())
            if position_list is None:
                time.sleep(0.1)
                continue
            set_flg = False
            return position_list
        except Exception as e:
            # print('get_position', datetime.now())
            # print(e)
            pass


# def get_history_positions(uniqueName, limit=10):
#     """
#     获取历史持仓数据。
#
#     :param uniqueName: 用户的唯一名称
#     :param limit: 返回记录的数量限制，默认为10
#     :return: 历史持仓的数据列表
#     """
#     # 获取当前时间戳，用于请求参数
#     now = int(time.time() * 1000)
#     # 构建请求URL
#     history_positions_url = f'https://www.okx.com/priapi/v5/ecotrade/public/history-positions?limit={limit}&uniqueName={uniqueName}&t={now}'
#     try:
#         # 发送GET请求
#         response = requests.get(history_positions_url, headers=get_header(), timeout=30)
#         # 解析JSON响应
#         history_positions_list = response.json().get('data', list())
#         return history_positions_list
#     except Exception as e:
#         print(f"获取历史持仓数据失败: {e}")
#         return []












if __name__ == '__main__':
    print(spider('2C3212F0BE59CC81'))
    # _list = spider('2C3212F0BE59CC81')
    # analysis_okx_follow(_list, _list)
    # 示例使用
    # uniqueName = "2C3212F0BE59CC81"
    # history_positions = get_history_positions(uniqueName)
    # print(history_positions)

    # print(spider('67A85F8BC1B67E17'))
    # print(spider('585D2CBB1B3E2A79'))
    # print(get_position('585D2CBB1B3E2A79'))
    # print(spider_close_item('032805718789399F'))
