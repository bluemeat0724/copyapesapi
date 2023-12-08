from celery import shared_task
from copytrade.celery import app as celery_app

# 记录日志：
import logging
logger = logging.getLogger("django")

# @shared_task(name="send_sms")
# def send_sms(tid, mobile, datas):
#     """异步发送短信"""
#     try:
#         logger.info(f"{tid}手机号：{mobile}，发送短信{datas}")
#     except Exception as e:
#         logger.error(f"手机号：{mobile}，发送短信失败错误: {e}")
#
#
# @shared_task(name="send_sms1")
# def send_sms1():
#     print("send_sms1执行了！！！")
@celery_app.task
def simple_task():
    print("执行了一个简单的任务")