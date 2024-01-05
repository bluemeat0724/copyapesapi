from crawler.myokx import app
# from okx import app
from okx.api.public import Public

# acc = {'key': '8af6ced4-5ea0-4dd9-9aef-f79529d72a68',
#        'secret': '6A840C3EC6D18D4E4127B13ADA7A1091',
#        'passphrase': '112233Ww..',
#        'proxies': {
#                     'http': 'socks5h://15755149931sct-5:8ivtkleb@38.45.108.138:5002',
#                     'https': 'socks5h://15755149931sct-5:8ivtkleb@38.45.108.138:5002'
#                    }
#        }
acc = {'key': 'fa6ff921-ae3d-42c7-b9f0-d10b3fcc26ec',
       'secret': 'DB5B7D108BFCB05A352FFA78053A099D',
       'passphrase': 'Newpasswd2024%',
       'proxies': {
                    'http': 'socks5h://xiaowen001:9zrn85g6@38.45.108.138:5002',
                    'https': 'socks5h://xiaowen001:9zrn85g6@38.45.108.138:5002'
                   }
       }


obj = app.OkxSWAP(**acc)
obj.account.api.flag = '1'
obj.trade.api.flag = '1'
#
# set_position_mode_result = obj.account.set_position_mode(
#                 posMode='long_short_mode')
# if set_position_mode_result['code'] == '0':
#     print('[SUCCESS] 设置持仓方式为双向持仓成功，posMode="long_short_mode"')
# else:
#     print('[FAILURE] 设置持仓方式为双向持仓失败，请手动设置：posMode="long_short_mode"')

#
# obj.trade.open_market(instId="IOST-USDT-SWAP", posSide="long", openMoney=10 * 10, tdMode='cross',
#                                   lever=10)

result = obj.trade.open_market(instId="BSV-USDT-SWAP", posSide="long", openMoney=100 * 10, tdMode='cross',
                                  lever=10)
# result = {'instType': 'SWAP', 'instId': 'ETH-USDT-SWAP', 'state': 'filled', 'ordId': '661695476885966848', 'meta': {}, 'request_param': {'instId': 'ETH-USDT-SWAP', 'tdMode': 'cross', 'posSide': 'long', 'side': 'buy', 'ordType': 'market', 'sz': '43', 'clOrdId': '', 'tag': ''}, 'func_param': {'instId': 'ETH-USDT-SWAP', 'tdMode': 'cross', 'posSide': 'long', 'lever': 10, 'openMoney': 1000, 'quantityCT': None, 'meta': {}, 'timeout': 60, 'delay': 0.2, 'cancel': True, 'clOrdId': '', 'tag': '', 'newThread': False, 'callback': None, 'errorback': None}, 'get_order_result': {'code': '0', 'data': {'accFillSz': '43', 'algoClOrdId': '', 'algoId': '', 'attachAlgoClOrdId': '', 'attachAlgoOrds': [], 'avgPx': '2301.58', 'cTime': '1704032495397', 'cancelSource': '', 'cancelSourceReason': '', 'category': 'normal', 'ccy': '', 'clOrdId': '', 'fee': '-0.4948397', 'feeCcy': 'USDT', 'fillPx': '2301.58', 'fillSz': '43', 'fillTime': '1704032495397', 'instId': 'ETH-USDT-SWAP', 'instType': 'SWAP', 'lever': '10', 'ordId': '661695476885966848', 'ordType': 'market', 'pnl': '0', 'posSide': 'long', 'px': '', 'pxType': '', 'pxUsd': '', 'pxVol': '', 'quickMgnType': '', 'rebate': '0', 'rebateCcy': 'USDT', 'reduceOnly': 'false', 'side': 'buy', 'slOrdPx': '', 'slTriggerPx': '', 'slTriggerPxType': '', 'source': '', 'state': 'filled', 'stpId': '', 'stpMode': '', 'sz': '43', 'tag': '', 'tdMode': 'cross', 'tgtCcy': '', 'tpOrdPx': '', 'tpTriggerPx': '', 'tpTriggerPxType': '', 'tradeId': '190117436', 'uTime': '1704032495398'}, 'msg': ''}, 'set_order_result': {'code': '0', 'data': {'clOrdId': '', 'ordId': '661695476885966848', 'sCode': '0', 'sMsg': 'Order placed', 'tag': ''}, 'inTime': '1704032495397180', 'msg': '', 'outTime': '1704032495398476'}, 'error_result': None, 'cancel_result': None}
# result ={'instType': 'SWAP', 'instId': 'BTC-USDT-SWAP', 'state': None, 'ordId': None, 'meta': {}, 'request_param': {'instId': 'BTC-USDT-SWAP', 'tdMode': 'cross', 'posSide': 'long', 'side': 'buy', 'ordType': 'market', 'sz': '23', 'clOrdId': '', 'tag': ''}, 'func_param': {'instId': 'BTC-USDT-SWAP', 'tdMode': 'cross', 'posSide': 'long', 'lever': 10, 'openMoney': 1000, 'quantityCT': None, 'meta': {}, 'timeout': 60, 'delay': 0.2, 'cancel': True, 'clOrdId': '', 'tag': '', 'newThread': False, 'callback': None, 'errorback': None}, 'get_order_result': None, 'set_order_result': {'code': '1', 'data': [{'clOrdId': '', 'ordId': '', 'sCode': '51010', 'sMsg': 'Request unsupported under current account mode ', 'tag': ''}], 'inTime': '1704032341348224', 'msg': 'All operations failed', 'outTime': '1704032341349427'}, 'error_result': {'code': 'FUNC_EXCEPTION', 'data': {}, 'msg': 'Traceback (most recent call last):\n  File "/Users/lichaoyuan/Desktop/copytrade/crawler/myokx/open.py", line 556, in inner_func\n    error_result = main_func(**main_data)\n  File "/Users/lichaoyuan/Desktop/copytrade/crawler/myokx/open.py", line 506, in main_func\n    ordId = set_order_result[\'data\'][\'ordId\']\nTypeError: list indices must be integers or slices, not str\n'}, 'cancel_result': None}

print(result)
try:
    s_code_value = result.get('set_order_result', {}).get('data', {}).get('sCode')
    if s_code_value == '0':
        print(s_code_value)
except:
    try:
        s_code_value = result.get('set_order_result', {}).get('data', [{}])[0].get('sCode')
        if s_code_value == '51010':
            print('账户模式不支持')
        elif s_code_value == '51011':
            print('账户余额不足')
        elif s_code_value == '51001':
            print('产品不存在')
        elif s_code_value == '51013':
            print('订单数量不合法')
    except:
        try:
            s_code_value = result.get('error_result', {}).get('code')
            if s_code_value == '51001':
                print('产品不存在')
        except:
            pass

# a = obj.trade.open_market(instId='DYDX-USDT-SWAP', posSide='long', openMoney=100,
#                                       tdMode='cross', lever=100)
# obj.trade.close_market(instId='ETH-USDT-SWAP', posSide='long', quantityCT=220, tdMode='cross')
# 当前持仓
# a = obj.account.get_positions()
# print(a)
# 历史持仓
# a = obj.account.get_positions_history(limit=10)
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
#        'http': 'socks5h://15755149931sct-5:8ivtkleb@38.147.173.111:5001',
#         'https': 'socks5h://15755149931sct-5:8ivtkleb@38.147.173.111:5001'
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
