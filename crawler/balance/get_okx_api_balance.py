from okx.api._client import ResponseStatusError

from crawler.myokx import app
from crawler.utils.db import Connect


def get_okx_api_balance(acc, flag, api_id):
    try:
        obj = app.OkxSWAP(**acc)
        obj.account.api.flag = flag
        obj.trade.api.flag = flag

        balance = obj.account.get_balance(ccy='BTC,ETH,USDT').get('data')[0].get('details')
    except ResponseStatusError as e:
        # 找到 "code" 的起始位置
        # Error response_status_code 401
        # response_content={"msg":"Request header OK-ACCESS-PASSPHRASE incorrect.","code":"50105"}
        start_index = e.find('"code":"') + len('"code":"')
        # 找到 "code" 的结束位置
        end_index = e.find('"', start_index)
        # 提取出 "code" 的值
        code_value = e[start_index:end_index]
        if code_value in ["50105", "50101", "50100"]:
            # api错误，进行逻辑删除
            with Connect() as db:
                db.exec("UPDATE api_apiinfo SET deleted = 1 WHERE id = %(api_id)s", api_id=api_id)
            print(f'api_id:{api_id} 已删除')
        return
    result = {}
    for item in balance:
        ccy = item.get('ccy')
        cashBal = item.get('cashBal')
        result[ccy] = cashBal
    update_balance(api_id, result)

# 更新api资产
def update_balance(api_id, balance):
    params = {
        'usdt': balance.get('USDT', 0),
        'btc': balance.get('BTC', 0),
        'eth': balance.get('ETH', 0),
        'api_id': api_id
    }

    update_sql = """
        UPDATE api_apiinfo
        SET 
            usdt = %(usdt)s,
            btc = %(btc)s,
            eth = %(eth)s
        WHERE id = %(api_id)s;
    """
    with Connect() as db:
        db.exec(update_sql, **params)


if __name__ == '__main__':
    acc = {'key': '8af6ced4-5ea0-4dd9-9aef-f79529d72a68',
           'secret': '6A840C3EC6D18D4E4127B13ADA7A1091',
           'passphrase': '112233Ww..',
           'proxies': {
                        'http': 'socks5h://15755149931sct-5:8ivtkleb@38.147.173.111:5001',
                        'https': 'socks5h://15755149931sct-5:8ivtkleb@38.147.173.111:5001'
                       }
           }
    flag = '1'
    api_id = 18
    get_okx_api_balance(acc, flag, api_id)
    # obj = app.OkxSWAP(**acc)
    # obj.account.api.flag = flag
    # obj.trade.api.flag = flag
    # obj.account.get_balance(ccy='BTC,ETH,USDT').get('data')[0].get('details')