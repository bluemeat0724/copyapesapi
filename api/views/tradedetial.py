from rest_framework.views import APIView
from rest_framework.response import Response
from api.extension import return_code
from api.models import SpiderLog, TradeLog


def format_log_data(log_queryset):
    """
    将日志记录的查询集转换为包含格式化日期时间字段的字典列表。
    """
    return [{
        'title': log.title,
        'date': log.date.strftime('%Y-%m-%d %H:%M:%S'),  # 手动格式化日期时间字段
        'description': log.description,
        'color': log.color
    } for log in log_queryset]


class TradeDetailView(APIView):
    def get(self, request, task_id):
        user_id = request.user.id
        # 从数据库中查询爬虫日志和交易日志
        spider_logs = SpiderLog.objects.filter(user_id=user_id, task_id=task_id).order_by('-date')
        trade_logs = TradeLog.objects.filter(user_id=user_id, task_id=task_id).order_by('-date')
        # 将查询结果转换为字典列表
        spider_data = format_log_data(spider_logs)
        trade_data = format_log_data(trade_logs)
        # 根据日志数据的存在与否返回不同的数据
        if spider_logs.exists() and not trade_logs.exists():
            return Response({"code": return_code.SUCCESS, "data": {'spider': spider_data, 'trade': []}})
        elif spider_logs.exists() and trade_logs.exists():
            return Response({"code": return_code.SUCCESS, "data": {'spider': spider_data, 'trade': trade_data}})
        else:
            return Response({"code": return_code.VALIDATE_ERROR, 'detail': '数据不存在！'})
