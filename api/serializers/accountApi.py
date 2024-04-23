from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from api import models


class ApiSerializer(serializers.ModelSerializer):
    # status = serializers.CharField(source="get_status_display", read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.ApiInfo
        fields = ['id', "platform", "api_name", "flag", "passPhrase", "api_key", "secret_key", "status", "user",
                  "create_datetime", 'acctLv', 'ip', 'roleType', 'level', 'perm', 'uid']
        # read_only_fields = ['status']
        extra_kwargs = {
            'passPhrase': {'write_only': True},
            # 'api_key': {'write_only': True},
            'secret_key': {'write_only': True},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 检查请求方法，如果是POST请求，将status字段设置为只读
        if self.context['request'].method == 'POST':
            self.fields['status'].read_only = True
