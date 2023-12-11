from crawler.utils.db import Connect
from crawler.utils.get_api import api
from crawler.myokx import app


class OkxOrderInfo(object):
    def __init__(self, user_id, task_id):
        self.user_id = user_id
        self.task_id = task_id
        self.api_id = self.get_api_id()
        # 通过api_id获取api信息
        self.acc, self.flag = api(self.user_id, self.api_id)

    # 获取api_id
    def get_api_id(self):
        with Connect() as conn:
            result = conn.fetch_one("select api_id from api_taskinfo where id = %(id)s",id={self.task_id})
            return result.get('api_id') if result else None

    # 获取当前持仓，同时往数据库写入或更新数据
    def get_position(self):
        try:
            obj = app.OkxSWAP(**self.acc)
        except:
            return
        obj.account.api.flag = self.flag
        data = obj.account.get_positions().get('data')
        for item in data:
            instId = item.get('instId')
            cTime = item.get('cTime')
            openAvgPx = item.get('avgPx')
            pnl = item.get('upl')
            pnlRatio = item.get('uplRatio')
            lever = item.get('lever')
            mgnMode = item.get('mgnMode')
            posSide = item.get('posSide')
            print(instId, cTime, openAvgPx, pnl, pnlRatio, lever, mgnMode, posSide)

            # 查询数据库，看是否存在具有相同 instId 和 cTime 的记录
            check_sql = "SELECT 1 FROM api_orderinfo WHERE instId = %(instId)s AND cTime = %(cTime)s LIMIT 1"
            with Connect() as db:
                record_exists = db.fetch_one(check_sql, instId=instId, cTime=cTime)

            params = {
                'user_id': self.user_id,
                'api_id': self.api_id,
                'instId': instId,
                'cTime': cTime,
                'openAvgPx': openAvgPx,
                'pnl': pnl,
                'pnlRatio': pnlRatio,
                'lever': lever,
                'mgnMode': mgnMode,
                'posSide': posSide
            }

            if record_exists:
                # 如果存在相同记录，执行更新操作
                update_sql = """
                                UPDATE api_orderinfo
                                SET
                                    pnl = %(pnl)s,
                                    pnlRatio = %(pnlRatio)s
                                WHERE instId = %(instId)s AND cTime = %(cTime)s;
                            """
                with Connect() as db:
                    db.exec(update_sql, **params)
            else:
                # 如果不存在相同记录，执行插入操作
                insert_sql = """
                                INSERT INTO api_orderinfo (user_id, api_id, instId, cTime, openAvgPx, pnl, pnlRatio, lever, mgnMode, posSide, status)
                                VALUES (%(user_id)s, %(api_id)s, %(instId)s, %(cTime)s, %(openAvgPx)s, %(pnl)s, %(pnlRatio)s, %(lever)s, %(mgnMode)s, %(posSide)s,1)
                            """
                with Connect() as db:
                    db.exec(insert_sql, **params)




if __name__ == '__main__':
    obj = OkxOrderInfo(1, 208)
    obj.get_position()


