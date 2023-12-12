from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from api import models


class TaskcSerializer(serializers.ModelSerializer):
    # status = serializers.CharField(source="get_status_display")
    # api = serializers.CharField(source="api.api_name")

    class Meta:
        model = models.TaskInfo
        fields = ['id', "trader_platform", "uniqueName", "api", "follow_type", "sums", "lever_set", "first_order_set",
                  'status', 'user', 'create_datetime', 'deleted','pnl']
        # read_only_fields = ['status']
        # extra_kwargs = {
        #     'status': {'read_only': True}
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 检查请求方法，如果是POST请求，将status字段设置为只读
        if self.context['request'].method == 'POST':
            self.fields['status'].read_only = True
