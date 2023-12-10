import os
from rest_framework.views import APIView
from rest_framework.response import Response
from api.extension import return_code

# 读取日志文件转换成字典
def log_to_dict(log_file_path):
    log_dict_list = []
    with open(log_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split(" | ")
            date, color, description = parts[0], parts[1], parts[2]
            # 分割标题和描述
            if '，' in description:
                title, desc = description.split('，', 1)
            else:
                title, desc = description, ''
            log_dict_list.append({
                'title': title,
                'date': date,
                'description': desc,
                'color': color
            })

    # 对日志列表按照日期进行倒序排序
    log_dict_list.sort(key=lambda x: x['date'], reverse=True)
    return log_dict_list

class TradeDetailView(APIView):
    def get(self, request, task_id):
        user_id = request.user.id

        # 本地环境路径
        abs = os.path.abspath(__file__)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(abs)))

        # 线上环境路径
        # base_dir = '/path/to/logs'

        spider_log_path = os.path.join(base_dir, 'crawler', 'spider_logs', f'{user_id}_{task_id}.log')
        trade_log_path = os.path.join(base_dir, 'crawler', 'trade_logs', f'{user_id}_{task_id}.log')

        if os.path.exists(spider_log_path) and not os.path.exists(trade_log_path):
            spider_data = log_to_dict(spider_log_path)
            return Response({"code": return_code.SUCCESS, "data": {'spider': spider_data, 'trade': []}})
        elif os.path.exists(spider_log_path) and os.path.exists(trade_log_path):
            spider_data = log_to_dict(spider_log_path)
            trade_data = log_to_dict(trade_log_path)
            return Response({"code": return_code.SUCCESS, "data": {'spider': spider_data, 'trade': trade_data}})
        else:
            return Response({"code": return_code.VALIDATE_ERROR, 'detail': '数据不存在！'})

