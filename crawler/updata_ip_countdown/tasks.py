from crawler.updata_ip_countdown.ip_countdown import get_countdown
from crawler.utils.db import Connect
from celery import shared_task


# 记录日志：
import logging

logger = logging.getLogger("celery")


@shared_task(name='get_ip_countdown')
def run_get_countdown():
    get_countdown()