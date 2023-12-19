"""
获取模拟盘和实盘的1张价值对比

如：BTC-USDT-SWAP
实盘'ctVal': '0.01'
模拟盘'ctVal': '0.001'
使用参数openMoney=100交易时，实盘保证金为100u，模拟盘保证金为10u

如：IOST-USDT-SWAP
实盘'ctVal': '1000'
模拟盘'ctVal': '1000'
使用参数openMoney=100交易时，实盘保证金为100u，模拟盘保证金为100u
"""
import requests


def get_trade_times(instId, api_flag, acc):
    # 实盘flag=0
    if api_flag == '0':
        return 1
    # 模拟盘flag=1
    if api_flag == '1':
        proxies = acc.get('proxies')
        url = f'https://www.okx.com/api/v5/public/instruments?instType=SWAP&instId={instId}'
        flag_0 = requests.get(url, headers={'x-simulated-trading': '0'}, proxies=proxies).json().get('data')[0].get(
            'ctVal')
        try:
            flag_1 = requests.get(url, headers={'x-simulated-trading': '1'}, proxies=proxies).json().get('data')[0].get(
                'ctVal')
        except:
            return None
        times = float(flag_0) / float(flag_1)
        return times


if __name__ == '__main__':
    acc = {'key': '8af6ced4-5ea0-4dd9-9aef-f79529d72a68', 'secret': '6A840C3EC6D18D4E4127B13ADA7A1091',
           'passphrase': '112233Ww..', 'proxies': {'http': 'socks5h://15755149931sct-5:8ivtkleb@38.147.173.111:5001',
                                                   'https': 'socks5h://15755149931sct-5:8ivtkleb@38.147.173.111:5001'}}
    instId = 'DYDX-USDT-SWAP'
    api_flag = '1'
    print(get_trade_times(instId, api_flag, acc))
