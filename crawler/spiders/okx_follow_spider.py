import sys
sys.path.append("D:\\my_source\\apes\\copyapesapi\\")
from crawler.utils.get_header import get_header
from crawler.utils.get_proxies import get_proxies
from datetime import datetime
import time
import requests


now = int(time.time()) * 1000


def spider(uniqueName, follow_type, task_id, trader_platform, sums, ratio, lever_set, first_order_set, api_id, user_id):
    summary_list_new = []
    url = f"https://www.okx.com/priapi/v5/ecotrade/public/position-summary?t={now}&uniqueName={uniqueName}&instType=SWAP"
    print(url)
    try:
        #  proxies=get_proxies()[0],
        data_list = requests.get(url, headers=get_header(), timeout=30).json().get('data', list())
        # data_list = requests.get(url, headers=get_header(), proxies=get_proxies()[0], timeout=30).json().get('data', list())
        if not data_list:
            return summary_list_new
        # 数据清洗
        for data in data_list:
            data_clear = {}
            # 处理爬虫返回的数据
            data_clear['availSubPos'] = float(data.get('availSubPos'))
            data_clear['margin'] = float(data.get('margin'))
            data_clear['instId'] = data.get('instId')
            data_clear['mgnMode'] = data.get('mgnMode')
            data_clear['posSide'] = data.get('posSide')
            data_clear['lever'] = data.get('lever')
            data_clear['openTime'] = data.get('openTime')
            data_clear['openAvgPx'] = data.get('openAvgPx')
            data_clear['uplRatio'] = float(data.get('pnlRatio'))

            # 添加原始数据
            data_clear['task_id'] = task_id
            data_clear['trader_platform'] = trader_platform
            data_clear['follow_type'] = follow_type
            data_clear['uniqueName'] = uniqueName
            data_clear['sums'] = sums
            data_clear['ratio'] = ratio
            data_clear['lever_set'] = lever_set
            data_clear['first_order_set'] = first_order_set
            data_clear['api_id'] = api_id
            data_clear['user_id'] = user_id
            summary_list_new.append(data_clear)
        return summary_list_new
    except Exception as e:
        # print('follow_spider', datetime.now())
        # print(e)
        pass


if __name__ == '__main__':
    print(spider('BFF709C3E154E021', 1, 1, 1, 1, 1, 1, 1, 1, 1))