import sys

sys.path.append("/Users/lichaoyuan/Desktop/copyapes/copyapesapi")
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
thirty_days_ago_specific_time = (_now - timedelta(days=30)).replace(
    hour=16, minute=0, second=0, microsecond=0
)
thirty_days_ago_specific_time_timestamp = (
    int(thirty_days_ago_specific_time.timestamp()) * 1000
)

# Get today's date at 16:00:00
today_specific_time = (_now + timedelta(days=2)).replace(
    hour=16, minute=0, second=0, microsecond=0
)
today_specific_time_timestamp = int(today_specific_time.timestamp()) * 1000


def spider(uniqueName):
    summary_list_new = []
    try:
        position_url = f"https://www.okx.com/priapi/v5/ecotrade/public/positions-v2?limit=10&uniqueName={uniqueName}&t={now}"
        position_list = (
            requests.get(position_url, headers=get_header(), timeout=30)
            .json()
            .get("data", [{}])[0]
            .get("posData", [])
        )

        if not position_list:
            return summary_list_new

        for item in position_list:
            data_clear = {
                "instId": item.get("instId"),
                "openTime": item.get("cTime"),  # 用于判断是否是最新的交易记录
                "posSide": item.get("posSide"),
                "lever": item.get("lever"),
                "pos": item.get("pos"),
                "openAvgPx": item.get("avgPx"),  # 冗余字段
                "mgnMode": item.get("mgnMode"),
                "uplRatio": item.get("uplRatio"),
                "posSpace": float(item.get("posSpace")),
            }
            pos = int(item.get("pos"))
            if data_clear["posSide"] == "net":
                if pos > 0:
                    data_clear["posSide"] = "long"
                elif pos < 0:
                    data_clear["posSide"] = "short"
            summary_list_new.append(data_clear)
        print(summary_list_new)
        return summary_list_new
    except Exception as e:
        print("personal_spider", datetime.now())
        print("1", e)
        pass


if __name__ == "__main__":
    print(spider("2C3212F0BE59CC81"))
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
