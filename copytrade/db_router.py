import random

class DBRouter(object):
    def db_for_read(self, model, **hints):
        """
        Reads go to a randomly-chosen replica, except for UserInfo model.
        """
        if model._meta.model_name == 'userinfo':
            return 'default'  # UserInfo 的读操作使用 'default' 数据库
        return random.choice(['read1',])

    def db_for_write(self, model, **hints):
        """
        Writes always go to primary.
        """
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the 'default' db is involved.
        """
        if obj1._state.db == 'default' or obj2._state.db == 'default':
            return True
        return None
