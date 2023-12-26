from crawler.utils.db import Connect
from crawler import settingsdev as settings
import redis

def calculate_and_stop_tasks():
    """根据任务类型计算累计收益和剩余额度，判断是否自动终止任务"""
    with Connect() as conn:
        tasks = conn.fetch_all("SELECT api_taskinfo.id, api_taskinfo.user_id, api_apiinfo.flag FROM api_taskinfo JOIN api_apiinfo WHERE api_taskinfo.status = 1 AND api_taskinfo.api_id = api_apiinfo.id")
        for task in tasks:
            task_id = task.get('id')
            user_id = task.get('user_id')
            flag = task.get('flag')

            # 计算累计收益
            total_pnl = calculate_total_pnl(user_id, flag)

            # 获取剩余额度
            remaining_quota = get_remaining_quota(user_id, flag)

            # 判断是否结束任务
            if total_pnl >= remaining_quota:
                stop_task(task_id)
                # 如果结束任务，则更新剩余额度，更新的动作在okx_orderinfo.py的get_position_history方法中
                # 避免重复调用此处只做标记
                task_pnl = check_task_pnl(task_id)
                remaining_quota -= task_pnl
                # update_remaining_quota(user_id, flag, remaining_quota)
                print(f"用户{user_id}的任务{task_id}盈利{task_pnl}，剩余额度{remaining_quota}，达到或达到过额度上限，任务自动结束。")


def calculate_total_pnl(user_id, flag):
    # 根据用户和任务类型计算累计收益的逻辑
    with Connect() as conn:
        result = conn.fetch_one(
            f"SELECT SUM(o.pnl) AS total_pnl "
            f"FROM api_taskinfo t "
            f"JOIN api_apiinfo a ON t.api_id = a.id "
            f"JOIN api_orderinfo o ON t.id = o.task_id "
            f"WHERE t.user_id = {user_id} AND t.status = 1 AND a.flag = {flag}"
        )
        return result['total_pnl'] if result and result['total_pnl'] else 0


def get_remaining_quota(user_id, flag):
    # 获取剩余额度的逻辑
    with Connect() as db:
        result = db.fetch_one(f"SELECT quota_{flag} AS remaining_quota FROM api_quotainfo WHERE user_id = {user_id}")
        return result['remaining_quota'] if result and result['remaining_quota'] else 0


def stop_task(task_id):
    # 手动将task_id的状态改为2
    with Connect() as db:
        db.exec(f"UPDATE api_taskinfo SET status = 2 WHERE id = {task_id}")
    # 往redis里的QUEUE_TASK_NAME写入task_id
    conn = redis.Redis(**settings.REDIS_PARAMS)
    conn.lpush(settings.QUEUE_TASK_NAME, task_id)

    # 将apiinfo的status改为1，释放api
    with Connect() as db:
        db.exec(f"UPDATE api_apiinfo SET status = 1 WHERE id = (SELECT api_id FROM api_taskinfo WHERE id = {task_id})")


def update_remaining_quota(user_id, flag, remaining_quota):
    update_quota_sql = f"""
                    UPDATE api_quotainfo
                    SET quota_{flag} = {remaining_quota} 
                    WHERE user_id = {user_id};
                """
    with Connect() as db:
        db.exec(update_quota_sql)

def check_task_pnl(task_id):
    with Connect() as db:
        result = db.fetch_one(
            f"SELECT pnl FROM api_taskinfo WHERE status = 2 AND id = {task_id}")['pnl']
        return result



if __name__ == '__main__':
    # calculate_and_stop_tasks()
    # print(calculate_total_pnl(1, 1))
    # print(get_remaining_quota(1, 1))
    # check_task_pnl(244)
    # update_remaining_quota(3,1,10)
    stop_task(261)