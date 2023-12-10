import requests
import time
from crawler.utils.get_proxies import get_proxies
from crawler.utils.get_header import get_header


now = int(time.time()) * 1000
def spider(uniqueName, follow_type, task_id, trader_platform, sums, lever_set, first_order_set, api_id, user_id):
    summary_list_new = []
    url = f'https://www.okx.com/priapi/v5/ecotrade/public/position-summary?t={now}&uniqueName={uniqueName}&instType=SWAP'
    try:
        data_list = requests.get(url, headers=get_header(), proxies=get_proxies(), timeout=30).json().get('data', list())
        if not data_list:
            return summary_list_new
        # 数据清洗
        for data in data_list:
            data_clear = {}
            # 处理爬虫返回的数据
            data_clear['availSubPos'] = data.get('availSubPos')
            data_clear['instId'] = data.get('instId')
            data_clear['mgnMode'] = data.get('mgnMode')
            data_clear['posSide'] = data.get('posSide')
            data_clear['lever'] = data.get('lever')
            data_clear['openTime'] = data.get('openTime')
            data_clear['openAvgPx'] = data.get('openAvgPx')

            # 添加原始数据
            data_clear['task_id'] = task_id
            data_clear['trader_platform'] = trader_platform
            data_clear['follow_type'] = follow_type
            data_clear['uniqueName'] = uniqueName
            data_clear['sums'] = sums
            data_clear['lever_set'] = lever_set
            data_clear['first_order_set'] = first_order_set
            data_clear['api_id'] = api_id
            data_clear['user_id'] = user_id
            summary_list_new.append(data_clear)
        return summary_list_new
    except:
        pass


if __name__ == '__main__':
    print(spider('31F08109D363843E', 1,1,1,1,1,1,1,1))