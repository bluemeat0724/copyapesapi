import requests
import time
from crawler.utils.get_header import get_header
from crawler.utils.get_proxies import get_my_proxies
import json

now = int(time.time()) * 1000


def spider(uniqueName):
    summary_list_new = []
    try:
        # proxies=get_my_proxies()[0],
        position_url = f"https://www.okx.com/priapi/v5/ecotrade/public/positions-v2?limit=10&uniqueName={uniqueName}&t={now}"
        position_res = requests.get(position_url, headers=get_header(), timeout=30).json()
        if int(position_res.get("code", 0)) == 0:
            position_list = position_res.get("data",
                                             [{}])[0].get("posData", [])

        else:
            # print("过快请求，请稍后再试", position_res)
            return None

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
                "upl_ratio": item.get("uplRatio"),
                "posSpace": float(item.get("posSpace")),
            }
            pos = int(item.get("pos"))
            if data_clear["posSide"] == "net":
                if pos > 0:
                    data_clear["posSide"] = "long"
                elif pos < 0:
                    data_clear["posSide"] = "short"
            summary_list_new.append(data_clear)
        return summary_list_new
    except Exception as e:
        # print("personal_spider", datetime.now())
        # print("1", e)
        pass


def person_history(uniqueName):
    history_dict = {}
    try:
        # 获取历史交易记录
        history_url = f"https://www.okx.com/priapi/v5/ecotrade/public/history-positions?limit=1&uniqueName={uniqueName}&t={now}"
        history_list = requests.get(history_url, headers=get_header(), timeout=30).json().get("data", [])
        # print("history_list", history_list)
        if not history_list:
            return history_dict

        #  key -> value
        #  instId-mgnMode -> cTime
        history_dict = {
            f"{item.get('instId')}-{item.get('mgnMode')}": item.get("uTime")
            for item in history_list
        }
        return history_dict
    except Exception as e:
        # print("personal_spider", datetime.now())
        # print("1", e)
        return {}


if __name__ == "__main__":
    # print(spider("563E3A78CDBAFB4E"))
    # print(person_history("563E3A78CDBAFB4E"))
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
    while True:
        # person_history("563E3A78CDBAFB4E")
        # spider('EE8655800B2F193F')
        print(spider("EE8655800B2F193F"))
        # time.sleep(3)
