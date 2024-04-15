from crawler import settingsdev as settings
import json
import redis
from crawler.trade import oktrade
from crawler.utils.reactivate_tasks import reactivate_trade_tasks
import threading

# 用字典映射任务ID和交易实例
traders = {}
traders_lock = threading.Lock()  # 创建一个线程锁，用于线程安全地访问和修改traders字典


def run_trade_task(task):
    task_id = task.get('task_id')
    trader_platform = task.get('trader_platform')
    status = task.get('status')

    # 根据status决定操作
    if status is None or status == 1:  # 假设status为None或1时表示启动或更新任务
        with traders_lock:  # 使用线程锁来确保线程安全
            if trader_platform == 1:
                trader = oktrade.Trader(**task)
                trader.start()
                # print(f"跟单任务{task_id}开始交易。")
            else:
                print(f"跟单任务{task_id}的交易平台不支持。")


    elif status in [2, 3]:  # 假设status为2,3时表示终止任务
        with traders_lock:
            trader = oktrade.Trader(**task)
            trader.status = status
            trader.stop()
            # 注意：由于在独立线程中执行，不再需要调用join()等待线程结束
            print(f"跟单任务{task_id}已结束。")



def run():
    print('交易脚本启动...')
    while True:
        try:
            conn = redis.Redis(**settings.REDIS_PARAMS)
            try:
                retrieved_json = conn.brpop(settings.TRADE_TASK_NAME, timeout=3)
            except:
                continue
            if not retrieved_json:
                continue
            task = json.loads(retrieved_json[1].decode('utf-8'))
            thread = threading.Thread(target=run_trade_task, args=(task,))
            thread.start()

        except Exception as e:
            print("trade脚本错误!")
            print(e)


if __name__ == '__main__':
    run()
