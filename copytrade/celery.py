import os
from celery import Celery
import logging

# 必须在实例化celery应用对象之前执行
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'copytrade.settings.settingsdev')


# 配置 Celery 日志
logger = logging.getLogger('celery')
logger.setLevel(logging.INFO)
logfile = os.path.join('logs', 'celery.log')
handler = logging.FileHandler(logfile)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# 实例化celery应用对象
app = Celery('copytrade')
# 指定任务的队列名称
app.conf.task_default_queue = 'Celery'
# 也可以把配置写在django的项目配置中
app.config_from_object('copytrade.settings.settingsdev', namespace='CELERY') # 设置django中配置信息以 "CELERY_"开头为celery的配置信息
# 自动根据配置查找django的所有子应用下的tasks任务文件
app.autodiscover_tasks()