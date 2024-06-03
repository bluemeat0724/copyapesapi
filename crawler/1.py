from crawler.myokx import app
# from okx import app
from okx.api.public import Public
import time

# 模拟子1
# acc = {'key': '2f071928-25bf-4ea9-b171-efe4b6e4eefd',
#        'secret': '0BE4E80811E950DBA93FA013D1F36516',
#        'passphrase': '112233Ww..',
#        # 'proxies': {
#        #              'http': 'socks5h://15755149931sct-5:8ivtkleb@14.29.122.97:10322',
#        #              'https': 'socks5h://15755149931sct-5:8ivtkleb@14.29.122.97:10322'
#        #             }
#        }
# 模拟子5
# acc = {'key': '5e773b21-f919-41f1-bdca-62834fbb2d03',
#        'secret': 'EC9399DC09F9C894F4E4E44EA66FA7C2',
#        'passphrase': '112233Ww..',
#        # 'proxies': {
#        #              'http': 'socks5h://15755149931sct-5:8ivtkleb@14.29.122.97:10322',
#        #              'https': 'socks5h://15755149931sct-5:8ivtkleb@14.29.122.97:10322'
#        #             }
#        }
# 模拟子2

# acc = {'key': '2842457e-1d17-4a58-a0d6-25d71044e75a',
#        'secret': 'A3A985254556CAAB007ABB15F7FECC9B',
#        'passphrase': '112233Ww..',
#        # 'proxies': {
#        #              'http': 'socks5h://15755149931sct-5:8ivtkleb@14.29.122.97:10322',
#        #              'https': 'socks5h://15755149931sct-5:8ivtkleb@14.29.122.97:10322'
#        #             }
#        }
# 模拟主1
# acc = {'key': 'ba8dccb8-943d-468c-bcbf-8dced96fc7cf',
#        'secret': 'BBA3FF14AC698CDBAA33219F858E7BF6',
#        'passphrase': '112233Ww..',
#        #    'proxies': {
#        #                 'http': 'socks5h://copyapes:12345678@18.167.134.231:5001',
#        #                 'https': 'socks5h://copyapes:12345678@18.167.134.231:5001'
#        #                }
#        }
acc = {'key': '5853686f-a0ed-4c76-a382-5ac480740883',
       'secret': '2DCFFF11C68C2E88C6437268B28A87FE',
       'passphrase': '112233Ww..',
    #    'proxies': {
    #                 'http': 'socks5h://copyapes:12345678@18.167.134.231:5001',
    #                 'https': 'socks5h://copyapes:12345678@18.167.134.231:5001'
    #                }
       }
# 模拟主1
# acc = {'key': 'ba8dccb8-943d-468c-bcbf-8dced96fc7cf',
#        'secret': 'BBA3FF14AC698CDBAA33219F858E7BF6',
#        'passphrase': '112233Ww..',
#     #    'proxies': {
#     #                 'http': 'socks5h://copyapes:12345678@18.167.134.231:5001',
#     #                 'https': 'socks5h://copyapes:12345678@18.167.134.231:5001'
#     #                }
#        }
# acc = {'key': '5853686f-a0ed-4c76-a382-5ac480740883',
#        'secret': '2DCFFF11C68C2E88C6437268B28A87FE',
#        'passphrase': '112233Ww..',
#        'proxies': {
#            'http': 'socks5h://copyapes:12345678@proxy.zhizhuip.com:5001',
#            'https': 'socks5h://copyapes:12345678@proxy.zhizhuip.com:5001'
#        }
#        }
# 实盘
# acc = {'key': '63b35cdd-261f-4fd5-ba2a-a607cd7460c9',
#        'secret': '52A5665FC31BFF7552D2980CE5C7F0F1',
#        'passphrase': '112233Ww..',
#        'proxies': {
#                     'http': 'socks5h://15755149931sct-5:8ivtkleb@14.29.122.97:10099',
#                     'https': 'socks5h://15755149931sct-5:8ivtkleb@14.29.122.97:10099'
#                    }
#        }
# 测试
# acc = {'key': '3fb304e4-2723-4b9a-aa86-7fbcb1661ac4',
#        'secret': 'DC44B17155DDEB723DF944D73632B6C2',
#        'passphrase': 'Rr749291263.',
#        }
# acc = {'key': 'da5fea7c-99e8-4892-9fdf-369a0d35fe6e',
#        'secret': '6A47EAA50207A62E332F9A1D1B3EF97C',
#        'passphrase': 'Yaoyao103123..',
#        'proxies': {
#                     'http': 'socks5h://15755149931sct-5:8ivtkleb@14.29.122.99:5001',
#                     'https': 'socks5h://15755149931sct-5:8ivtkleb@14.29.122.99:5001'
#                    }
#        }

#
obj = app.OkxSWAP(**acc)
obj.account.api.flag = '1'
obj.trade.api.flag = '1'
start_time = time.time()
# 查看账户配置信息
print(obj.account.get_config())

# a = obj.account.get_positions_history(limit=1)
# print(a)

# set_position_mode_result = obj.account.set_position_mode(
#                 posMode='long_short_mode')
# if set_position_mode_result['code'] == '0':
#     print('[SUCCESS] 设置持仓方式为双向持仓成功，posMode="long_short_mode"')
# else:
#     print('[FAILURE] 设置持仓方式为双向持仓失败，请手动设置：posMode="long_short_mode"')
#
#

#
# a = obj.trade.open_market(instId="DOGE-USDT-SWAP", posSide="long", openMoney=28800, tdMode='cross',
#                           lever=50)
# end_time = time.time()
# t = start_time - end_time
# print(a)
# print(t)
# from crawler.utils.get_trade_times import get_trade_times
# trade_times = get_trade_times("ETH-USDT-SWAP", '1', acc)
# print(trade_times)
# result = obj.trade.open_market(instId="BTC-USDT-SWAP", posSide="long", openMoney=10*trade_times, tdMode='cross',
#                                   lever=5)
# result = {'instType': 'SWAP', 'instId': 'LTC-USDT-SWAP', 'state': None, 'ordId': None, 'meta': {}, 'request_param': {'instId': 'LTC-USDT-SWAP', 'tdMode': 'cross', 'posSide': 'long', 'side': 'buy', 'ordType': 'market', 'sz': '0', 'clOrdId': '', 'tag': ''}, 'func_param': {'instId': 'LTC-USDT-SWAP', 'tdMode': 'cross', 'posSide': 'long', 'lever': 3, 'openMoney': 5, 'quantityCT': None, 'meta': {}, 'timeout': 60, 'delay': 0.2, 'cancel': True, 'clOrdId': '', 'tag': '', 'newThread': False, 'callback': None, 'errorback': None}, 'get_order_result': None, 'set_order_result': {'code': '1', 'data': [{'clOrdId': '', 'ordId': '', 'sCode': '51000', 'sMsg': 'Parameter sz error', 'tag': ''}], 'inTime': '1704986885902318', 'msg': 'All operations failed', 'outTime': '1704986885902391'}, 'error_result': {'code': 'FUNC_EXCEPTION', 'data': {}, 'msg': 'Traceback (most recent call last):\n  File "/Users/lichaoyuan/Desktop/copytrade/crawler/myokx/open.py", line 557, in inner_func\n    error_result = main_func(**main_data)\n  File "/Users/lichaoyuan/Desktop/copytrade/crawler/myokx/open.py", line 507, in main_func\n    ordId = set_order_result[\'data\'][\'ordId\']\nTypeError: list indices must be integers or slices, not str\n'}, 'cancel_result': None}
# print(result)

#
# get_ticker_result = obj.trade._market.get_ticker(instId="ETH-USDT-SWAP")
# print(get_ticker_result)
# openPrice = float(get_ticker_result['data']['askPx'])
# print(openPrice)
# get_quantity_result = obj.trade.get_quantity(
#                         openPrice=openPrice, openMoney=3668.28*trade_times,
#                         instId="ETH-USDT-SWAP", ordType='market',
#                         leverage=20,
#                     )
# print('get_quantity_result',get_quantity_result['data'],type(get_quantity_result['data']))
# exchangeInfo = obj.trade._market.get_exchangeInfo(
#             instId="W-USDT-SWAP",
#             expire_seconds=60 * 5
#         )
# ctVal = exchangeInfo['data']['ctVal']
# print(ctVal)
# quantity = 1*trade_times * 5 / openPrice / float(ctVal)
# print(quantity)
# stepSize = exchangeInfo['data']['lotSz']
# import math
# if float(stepSize) >= 1:
#     quantity = math.floor(quantity)
#     print('1', quantity)
# else:
#     quantity = math.floor(quantity * 10) / 10
#     print('0', quantity)

#
# a = obj.trade.close_market(instId="ETH-USDT-SWAP", posSide='long', quantityCT=get_quantity_result['data'],
#                                         tdMode='cross')
# print(a)


# try:
#     s_code_value = result.get('set_order_result', {}).get('data', {}).get('sCode')
#     if s_code_value == '0':
#         print(s_code_value)
# except:
#     try:
#         s_code_value = result.get('set_order_result', {}).get('data', [{}])[0].get('sCode')
#         if s_code_value == '51000':
#             print('账户模式不支持')
#         elif s_code_value == '51011':
#             print('账户余额不足')
#         elif s_code_value == '51001':
#             print('产品不存在')
#         elif s_code_value == '51013':
#             print('订单数量不合法')
#     except:
#         try:
#             s_code_value = result.get('error_result', {}).get('code')
#             if s_code_value == '51001':
#                 print('产品不存在')
#         except:
#             pass

# a = obj.trade.open_market(instId='ETH-USDT-SWAP', posSide='long', openMoney=100,
#                                       tdMode='cross', lever=100)
# obj.trade.close_market(instId='ETH-USDT-SWAP', posSide='long', quantityCT=220, tdMode='cross')
# 当前持仓
# a = obj.account.get_positions()
# print(a)
# 历史持仓
# a = obj.account.get_positions_history(limit=2)
# print(a)
# 账户信息
# a = obj.account.get_balance(ccy='BTC,ETH,USDT').get('data')[0].get('details') # 限速：10次/2s
# result = {}

# for item in a:
#     ccy = item.get('ccy')
#     cashBal = item.get('cashBal')
#     result[ccy] = cashBal
# # print(result)
# bnb = result.get('BNB', 0)
# print(bnb)


# 基础信息
# a = Public().get_instruments(instType='SWAP')


#
# import requests
#
# proxies = {
#        'http': 'socks5h://15755149931sct-5:8ivtkleb@18.167.134.231:5001',
#         'https': 'socks5h://15755149931sct-5:8ivtkleb@18.167.134.231:5001'
#        }
#
# a = requests.get(url = 'https://www.okx.com/api/v5/public/instruments?instType=SWAP&instId=DYDX-USDT-SWAP',headers={'x-simulated-trading': '1'},proxies=proxies).json()

# print(a)

"""
实盘信息
{'code': '0', 
 'data': [
            {'adl': '1', 'availPos': '199', 'avgPx': '0.10045', 'baseBal': '', 'baseBorrowed': '', 'baseInterest': '',
             'bePx': '0.1005505002501251', 'bizRefId': '', 'bizRefType': '', 'cTime': '1702229518344', 'ccy': 'USDT',
             'closeOrderAlgo': [], 'deltaBS': '', 'deltaPA': '', 'fee': '-0.09994775', 'fundingFee': '0', 'gammaBS': '',
             'gammaPA': '', 'idxPx': '0.100373', 'imr': '', 'instId': 'DOGE-USDT-SWAP', 'instType': 'SWAP', 'interest': '',
             'last': '0.10045', 'lever': '3', 'liab': '', 'liabCcy': '', 'liqPenalty': '0', 'liqPx': '0.0673870202781967',
             'margin': '66.6318333333333333', 'markPx': '0.10046', 'mgnMode': 'isolated', 'mgnRatio': '60.618126315916484',
             'mmr': '0.999577', 'notionalUsd': '199.96537885', 'optVal': '', 'pendingCloseOrdLiabVal': '', 'pnl': '0',
             'pos': '199', 'posCcy': '', 'posId': '654133243020668928', 'posSide': 'long', 'quoteBal': '', 'quoteBorrowed': '',
             'quoteInterest': '', 'realizedPnl': '-0.09994775', 'spotInUseAmt': '', 'spotInUseCcy': '', 'thetaBS': '',
             'thetaPA': '', 'tradeId': '30646646', 'uTime': '1702229518344', 'upl': '0.0198999999999923', 'uplLastPx': '0',
             'uplRatio': '0.0002986560477851', 'uplRatioLastPx': '0', 'usdPx': '', 'vegaBS': '', 'vegaPA': ''},

            {'adl': '1', 'availPos': '27', 'avgPx': '73.18', 'baseBal': '', 'baseBorrowed': '', 'baseInterest': '',
             'bePx': '73.2312516258129', 'bizRefId': '', 'bizRefType': '', 'cTime': '1702228492444', 'ccy': 'USDT',
             'closeOrderAlgo': [], 'deltaBS': '', 'deltaPA': '', 'fee': '-0.0395172', 'fundingFee': '0', 'gammaBS': '',
             'gammaPA': '', 'idxPx': '72.6786', 'imr': '', 'instId': 'SOL-USDT-SWAP', 'instType': 'SWAP', 'interest': '',
             'last': '72.7', 'lever': '3', 'liab': '', 'liabCcy': '', 'liqPenalty': '0', 'liqPx': '49.06647729177141',
             'margin': '65.862', 'markPx': '72.71', 'mgnMode': 'isolated', 'mgnRatio': '59.82254118686518', 'mmr': '0.981585',
             'notionalUsd': '196.36607925', 'optVal': '', 'pendingCloseOrdLiabVal': '', 'pnl': '0', 'pos': '27', 'posCcy': '',
             'posId': '654128940084195328', 'posSide': 'long', 'quoteBal': '', 'quoteBorrowed': '', 'quoteInterest': '',
             'realizedPnl': '-0.0395172', 'spotInUseAmt': '', 'spotInUseCcy': '', 'thetaBS': '', 'thetaPA': '',
             'tradeId': '46349075', 'uTime': '1702228492444', 'upl': '-1.2690000000000354', 'uplLastPx': '-1.296000000000011',
             'uplRatio': '-0.0192675594424713', 'uplRatioLastPx': '-0.0196775075157147', 'usdPx': '', 'vegaBS': '',
             'vegaPA': ''}
         ], 
 'msg': ''
 }

 历史持仓
 {'code': '0', 'data': [], 'msg': ''}
 {
    'code': '0', 
     'data': [
                {'cTime': '1702256227724', 'ccy': 'USDT', 'closeAvgPx': '2277.59', 'closeTotalPos': '3849', 'direction': 'long',
                 'fee': '-88.77616815', 'fundingFee': '0', 'instId': 'ETH-USDT-SWAP', 'instType': 'SWAP', 'lever': '100.0',
                 'liqPenalty': '-350.6577564', 'mgnMode': 'cross', 'openAvgPx': '2335.3571628994544037', 'openMaxPos': '3849',
                 'pnl': '-2223.4581', 'pnlRatio': '-2.9624589154923515', 'posId': '651930173952069635',
                 'realizedPnl': '-2662.89202455', 'triggerPx': '2277.59', 'type': '3', 'uTime': '1702260761272', 'uly': 'ETH-USDT'},
                {'cTime': '1702232959213', 'ccy': 'USDT', 'closeAvgPx': '2345.3531862938164632', 'closeTotalPos': '2539',
                 'direction': 'short', 'fee': '-59.7383012', 'fundingFee': '12.852102471434275', 'instId': 'ETH-USDT-SWAP',
                 'instType': 'SWAP', 'lever': '100.0', 'liqPenalty': '0', 'mgnMode': 'cross', 'openAvgPx': '2360.3026782197715636',
                 'openMaxPos': '2539', 'pnl': '379.5676', 'pnlRatio': '0.555134376931007', 'posId': '649318532001398784',
                 'realizedPnl': '332.681401271434275', 'triggerPx': '', 'type': '2', 'uTime': '1702256168356', 'uly': 'ETH-USDT'}
            ], 
     'msg': ''
 }


 """

"""
'instId':'ETH-USDT-SWAP',

'cTime': '1702256227724',    开仓时间
'uTime': '1702260761272',    平仓时间
'openAvgPx': '2335.3571628994544037',     开仓均价avgPx
'closeAvgPx': '2277.59',     平仓均价
'pnl': '-2223.4581',       收益
'pnlRatio': '-2.9624589154923515',       收益率

'lever': '100.0',       杠杆
'mgnMode': 'cross',     全仓   isolated：逐仓

'posSide': 'long',   当前订单持仓方向
'direction': 'long'，  历史订单持仓方向

imr 持仓量（当前）  openMaxPos最大持仓量（历史）

"""
# from okx.api.trade import Trade
#
# # API 初始化
# apikey = "2f071928-25bf-4ea9-b171-efe4b6e4eefd"
# secretkey = "0BE4E80811E950DBA93FA013D1F36516"
# passphrase = "112233Ww.."
#
# flag = "1"  # 实盘: 0, 模拟盘: 1
#
# tradeAPI = Trade(apikey, secretkey, passphrase, flag)
#
# # 查询币币历史订单（7天内）
# # 已经撤销的未成交单 只保留2小时
# result = tradeAPI.get_orders_history(
#     instType="SWAP",
#     state='canceled'
# )
# print(result)