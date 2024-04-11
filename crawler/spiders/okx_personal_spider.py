import requests
import time
from datetime import datetime, timedelta, timezone
from crawler.utils.get_header import get_header
from crawler.utils.get_proxies import get_proxies


now = int(time.time()) * 1000

# 获取当前日期和时间
_now = datetime.now(timezone.utc)

# 获取昨天的日期，时间设为15:59:59
yesterday_specific_time = (_now - timedelta(days=30)).replace(hour=16, minute=0, second=0, microsecond=0)
yesterday_specific_time_timestamp = int(yesterday_specific_time.timestamp()) * 1000

# Get today's date at 16:00:00
today_specific_time = _now.replace(hour=16, minute=0, second=0, microsecond=0)
today_specific_time_timestamp = int(today_specific_time.timestamp()) * 1000

# uniqueName = '563E3A78CDBAFB4E'
# uniqueName = 'C343256953163322'

def spider(uniqueName):
    summary_list_new = []
    data_clear = {}
    try:
        position_url = f'https://www.okx.com/priapi/v5/ecotrade/public/positions-v2?limit=10&uniqueName={uniqueName}&t={now}'
        position_list = requests.get(position_url, headers=get_header(), timeout=30).json().get('data', list())[0].get('posData', list())
        # print(position_list)
        if not position_list:
            return summary_list_new

        record_url = f'https://www.okx.com/priapi/v5/ecotrade/public/trade-records?limit=1&startModify={yesterday_specific_time_timestamp}&endModify={today_specific_time_timestamp}&uniqueName={uniqueName}&t={now}'
        record_list = requests.get(record_url, headers=get_header(), timeout=30).json().get('data', list())
        print(record_list)
        data_clear['instId'] = record_list[0].get('instId')
        data_clear['openTime'] = record_list[0].get('cTime')  # 用于判断是否是最新的交易记录
        data_clear['posSide'] = record_list[0].get('posSide')
        data_clear['lever'] = record_list[0].get('lever')
        data_clear['openAvgPx'] = record_list[0].get('avgPx') # 冗余字段
        # data_clear['side'] = record_list[0].get('side')

        exist = False
        for item in position_list:
            if item.get('instId') == record_list[0].get('instId') and item.get('posSide') == record_list[0].get('posSide'):
                data_clear['mgnMode'] = item.get('mgnMode')
                exist = True
                if record_list[0].get('side') == 'buy':
                    data_clear['order_type'] = 'open'
                else:
                    data_clear['order_type'] = 'reduce'  # 减仓

        if not exist:
            data_clear['order_type'] = 'close'  # 平仓
        summary_list_new.append(data_clear)
        return summary_list_new
    except Exception as e:
        print(e)


if __name__ == '__main__':
    print(spider('C343256953163322'))
