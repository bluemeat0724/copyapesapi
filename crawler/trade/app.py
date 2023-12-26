from crawler import settingsdev as settings
import json
import redis
from crawler.trade import oktrade
from crawler.utils.reactivate_tasks import reactivate_trade_tasks

# 用字典映射任务ID和交易实例
traders = {}


def run():
    # 恢复交易爬虫
    reactivate = reactivate_trade_tasks()
    if reactivate:
        for task in reactivate:
            task_id = task.get('task_id')
            trader_platform = task.get('trader_platform')
            if trader_platform == 1:
                trader = oktrade.Trader(**task)
                trader.start()
                traders[task_id] = trader
                print(f"任务{task_id}交易实例已恢复。")
            else:
                print(f"跟单任务{task_id}的交易平台不支持。")

    while True:
        try:
            # 去redis里获取跟单任务id
            conn = redis.Redis(**settings.REDIS_PARAMS)
            try:
                retrieved_json = conn.brpop(settings.TRADE_TASK_NAME, timeout=3)
            except:
                continue
            if not retrieved_json:
                continue
            retrieved_json = retrieved_json[1].decode('utf-8')
            retrieved_dict = json.loads(retrieved_json)  # 解析任务的字典

            print(retrieved_dict)
            status = retrieved_dict.get('status')
            task_id = retrieved_dict.get('task_id')
            trader_platform = retrieved_dict.get('trader_platform')

            if status is None:
                # 交易进程启动
                if task_id not in traders:
                    if trader_platform == 1:
                        trader = oktrade.Trader(**retrieved_dict)
                    else:
                        print(f"跟单任务{task_id}的交易平台不支持。")
                        continue
                    trader.start()
                    traders[task_id] = trader
                    print(f"跟单任务{task_id}开始交易。")
                else:
                    # 在原有进程中直接进行交易
                    trader = traders[task_id]
                    trader.update_data(retrieved_dict)

            # 交易进程终止
            elif status == 2:
                if task_id in traders:
                    trader = traders.pop(task_id)
                    trader.stop()
                    trader.join()
                    print(f"跟单任务{task_id}已结束。")
                else:
                    print(f"跟单任务{task_id}不存在。")


        except (SyntaxError, NameError):
            print("数据错误！")


if __name__ == '__main__':
    run()