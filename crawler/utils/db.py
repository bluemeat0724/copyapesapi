import pymysql
from crawler import settingsprod as settings
from pymysql.cursors import DictCursor


class Connect(object):
    def __init__(self):
        self.conn = conn = pymysql.connect(**settings.MYSQL_CONN_PARAMS)
        self.cursor = conn.cursor(pymysql.cursors.DictCursor)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.conn.close()

    # 数据库更新
    def exec(self, sql, **kwargs):
        self.cursor.execute(sql, kwargs)
        self.conn.commit()

    # 获取单条数据
    def fetch_one(self, sql, **kwargs):
        self.cursor.execute(sql, kwargs)
        result = self.cursor.fetchone()
        return result

    # 获取全部数据
    def fetch_all(self, sql, **kwargs):
        self.cursor.execute(sql, kwargs)
        result = self.cursor.fetchall()
        return result
