import requests
from functools import wraps
import time
from okx import app
from okx import api


def retry(max_attempts=5, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:  # 捕获所有异常
                    print(f"操作失败，原因: {e}. 正在重试...")
                    attempts += 1
                    time.sleep(delay)
            print("多次尝试失败，继续执行程序的其他部分。")
        return wrapper
    return decorator

class RetryDecoratorProxy:
    def __init__(self, obj):
        self._obj = obj

    def __getattr__(self, name):
        attr = getattr(self._obj, name)
        if callable(attr):
            return retry()(attr)
        return attr

class RetryNetworkOperations:
    def __init__(self, network_operations):
        self._operations = network_operations

    def __getattr__(self, name):
        attr = getattr(self._operations, name)
        # 如果 attr 是对象实例，为其方法应用 retry 装饰器
        if not callable(attr) and not name.startswith("__"):
            return RetryDecoratorProxy(attr)
        return attr


acc = {
    'key': 'dfe2ebb7-d9fb-44d0-ab7c-f54739e5b92e',
    'secret': '3FAC73A01976ED04C31FE07A718A0BC1',
    'passphrase': '112233Ww..',
}

obj = RetryNetworkOperations(app.OkxSWAP(**acc))

obj.account.api.flag = '1'
obj.trade.api.flag = '1'
# print(obj)
# okx源码被注释部分，先初始化账户开平仓模式
# set_position_mode_result = obj.account.set_position_mode(posMode='long_short_mode')
# if set_position_mode_result['code'] == '0':
#     print('[SUCCESS] 设置持仓方式为双向持仓成功，posMode="long_short_mode"')
# else:
#     print('[FAILURE] 设置持仓方式为双向持仓失败，请手动设置：posMode="long_short_mode"')

# b = obj.account.get_balances()
# print(b)
a = obj.trade.open_market(instId='ETH-USDT-SWAP', posSide='short', openMoney= 1000, tdMode='cross', lever=20)
# print(a)

# obj = api.API(**acc)
# a = obj.trade.set_order(instId='ETH-USDT-SWAP', sz= 1000, tdMode='cross', side='buy', ordType='limit')
print(a)