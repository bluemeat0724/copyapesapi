from crawler.utils.db import Connect


# api所有已完成的任务pnl，未未完成任务upl
def update_api_pnl(api_id):
    # 已实现pnl
    update_pnl_sql = """
                UPDATE api_apiinfo
                SET pnl = COALESCE((SELECT SUM(pnl) FROM api_taskinfo WHERE status = 2 AND api_id = %(api_id)s), 0)
                WHERE id = %(api_id)s;
            """
    with Connect() as db:
        db.exec(update_pnl_sql, api_id=api_id)

    # 未实现upl
    update_upl_sql = """
                UPDATE api_apiinfo
                SET upl = COALESCE((SELECT SUM(pnl) FROM api_taskinfo WHERE status = 1 AND api_id = %(api_id)s), 0)
                WHERE id = %(api_id)s;
            """
    with Connect() as db:
        db.exec(update_upl_sql, api_id=api_id)

# 用户所有api的pnl，区分实盘和模拟盘
def update_user_pnl(user_id):
    # 实盘pnl
    update_pnl_sql = """
                UPDATE api_quotainfo
                SET pnl_0 = (SELECT SUM(pnl) FROM api_apiinfo WHERE user_id = %(user_id)s AND flag = 0)
                WHERE user_id = %(user_id)s;
            """
    with Connect() as db:
        db.exec(update_pnl_sql, user_id=user_id)

    # 模拟盘pnl
    update_pnl_sql = """
                UPDATE api_quotainfo
                SET pnl_1 = (SELECT SUM(pnl) FROM api_apiinfo WHERE user_id = %(user_id)s AND flag = 1)
                WHERE user_id = %(user_id)s;
            """
    with Connect() as db:
        db.exec(update_pnl_sql, user_id=user_id)

    # 实盘upl
    update_upl_sql = """
                UPDATE api_quotainfo
                SET upl_0 = (SELECT SUM(upl) FROM api_apiinfo WHERE user_id = %(user_id)s AND flag = 0)
                WHERE user_id = %(user_id)s;
            """
    with Connect() as db:
        db.exec(update_upl_sql, user_id=user_id)

    # 模拟盘upl
    update_upl_sql = """
                UPDATE api_quotainfo
                SET upl_1 = (SELECT SUM(upl) FROM api_apiinfo WHERE user_id = %(user_id)s AND flag = 1)
                WHERE user_id = %(user_id)s;
            """
    with Connect() as db:
        db.exec(update_upl_sql, user_id=user_id)


if __name__ == '__main__':
    # 第一步：更新api所有已完成的任务pnl
    update_api_pnl(2)
    # 第二步：更新用户所有api的pnl，区分实盘和模拟盘
    # update_user_pnl(1)