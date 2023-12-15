from crawler.utils.db import Connect
from crawler.utils.get_api import api
from crawler.myokx import app
import time


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

    # 查询数据库，看是否存在具有相同 instId 和 cTime 的记录
    def check_order(self, instId, cTime):
        check_sql = "SELECT 1 FROM api_orderinfo WHERE instId = %(instId)s AND cTime = %(cTime)s LIMIT 1"
        with Connect() as db:
            record_exists = db.fetch_one(check_sql, instId=instId, cTime=cTime)
            return record_exists

    # 查询当前任务下所有正在进行中的交易
    def get_order(self):
        with Connect() as db:
            result = db.fetch_all("select * from api_orderinfo where user_id = %(user_id)s and task_id = %(task_id)s and status = 1", user_id=self.user_id, task_id=self.task_id)
            return result

    # 手动跟新taskinfo表中关联orderinfo中的pnl数据
    def update_pnl(self):
        update_pnl_sql = """
            UPDATE api_taskinfo
            SET pnl = (SELECT SUM(pnl) FROM api_orderinfo WHERE task_id = %(task_id)s AND user_id = %(user_id)s)
            WHERE id = %(task_id)s AND user_id = %(user_id)s;
        """
        with Connect() as db:
            db.exec(update_pnl_sql, task_id=self.task_id, user_id=self.user_id)

    # 获取当前持仓，同时往数据库写入或更新数据
    def get_position(self):
        """
        限速：10次/2s

        通过celery定期执行
        :return:
        """
        try:
            obj = app.OkxSWAP(**self.acc)
        except:
            return
        obj.account.api.flag = self.flag
        data = obj.account.get_positions().get('data')
        # print(data)
        # 如果没有数据，说明已经全部平仓，跟新所有交易数据
        if not data:
            self.get_position_history()
            return
        for item in data:
            instId = item.get('instId')
            cTime = item.get('cTime')
            openAvgPx = item.get('avgPx')
            pnl = item.get('upl')
            pnlRatio = item.get('uplRatio')
            lever = item.get('lever')
            mgnMode = item.get('mgnMode')
            posSide = item.get('posSide')
            imr = item.get('imr', 0)
            # print(instId, cTime, openAvgPx, pnl, pnlRatio, lever, mgnMode, posSide)

            # 查询数据库，看是否存在具有相同 instId 和 cTime 的记录
            record_exists = self.check_order(instId, cTime)

            params = {
                'user_id': self.user_id,
                'task_id': self.task_id,
                'api_id': self.api_id,
                'instId': instId,
                'cTime': cTime,
                'openAvgPx': openAvgPx,
                'pnl': pnl,
                'pnlRatio': pnlRatio,
                'lever': lever,
                'mgnMode': mgnMode,
                'posSide': posSide,
                'imr': imr
            }

            if record_exists:
                # 如果存在相同记录，执行更新操作
                update_sql = """
                                UPDATE api_orderinfo
                                SET
                                    pnl = %(pnl)s,
                                    imr = %(imr)s,
                                    pnlRatio = %(pnlRatio)s
                                WHERE instId = %(instId)s AND cTime = %(cTime)s;
                            """
                with Connect() as db:
                    db.exec(update_sql, **params)
                self.update_pnl()
            else:
                # 如果不存在相同记录，执行插入操作
                insert_sql = """
                                INSERT INTO api_orderinfo (user_id, task_id, api_id, instId, cTime, openAvgPx, pnl, imr, pnlRatio, lever, mgnMode, posSide, status)
                                VALUES (%(user_id)s, %(task_id)s, %(api_id)s, %(instId)s, %(cTime)s, %(openAvgPx)s, %(pnl)s, %(imr)s, %(pnlRatio)s, %(lever)s, %(mgnMode)s, %(posSide)s,1)
                            """
                with Connect() as db:
                    db.exec(insert_sql, **params)
                self.update_pnl()

    # 当发生平仓交易时，检查交易所账户历史数据，并更新数据库
    def get_position_history(self):
        """
        限速：1次/10s

        触发时机：跟单时发生平仓交易、以及结束跟单任务时
        业务逻辑：1.检索数据库，找到当前跟单任务下正在进行中的交易（status=1），提取instId和cTime
                2.获取交易所的历史数据
                3.如果提取instId和cTime在历史交易数据中也出现，则更新uTime，stauts等数据
        """
        # 检索数据库
        ongoing_data = self.get_order()
        # 获取账户历史订单
        try:
            obj = app.OkxSWAP(**self.acc)
        except:
            return
        obj.account.api.flag = self.flag

        max_retries = 3  # 设置最大重试次数
        retries = 0
        while retries < max_retries:
            try:
                # 查看前5条交易记录
                history_data = obj.account.get_positions_history(limit='10').get('data')
            except:
                retries += 1
                time.sleep(10)

        if not history_data:
            return

        # 将 history_data 转换为字典，以便快速检查 instId 和 cTime 是否匹配
        history_data_dict = {(item['instId'], int(item['cTime'])): item for item in history_data}

        # 筛选出在 history_data 中并且在 ongoing_data 中存在的数据
        matching_data = [history_data_dict.get((str(item['instId']), item['cTime']), None) for item in ongoing_data]

        # 去除匹配数据中的 None
        matching_data = [item for item in matching_data if item is not None]

        if not matching_data:
            return
        # 跟新数据
        for item in matching_data:
            params = {
                'instId': item.get('instId'),
                'cTime': int(item.get('cTime')),
                'uTime': int(item.get('uTime')),
                'pnl': item.get('realizedPnl'),
                'pnlRatio': item.get('pnlRatio'),
                'closeAvgPx': item.get('closeAvgPx'),
                'imr': float(item.get('realizedPnl'))/float(item.get('pnlRatio')),
                'status': 2
            }
            update_sql = """
                            UPDATE api_orderinfo
                            SET
                                uTime = %(uTime)s,
                                pnl = %(pnl)s,
                                pnlRatio = %(pnlRatio)s,
                                closeAvgPx = %(closeAvgPx)s,
                                imr = %(imr)s,
                                status = %(status)s
                            WHERE instId = %(instId)s AND cTime = %(cTime)s;
                        """
            with Connect() as db:
                db.exec(update_sql, **params)
            self.update_pnl()





if __name__ == '__main__':
    obj = OkxOrderInfo(1, 224)
    obj.get_position()


