from api import models
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from api.extension import return_code

class OrderInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrderInfo
        fields = '__all__'

class OrderView(APIView):
    """合约交易列表"""

    def get(self, request, task_id):
        user_id = request.user.id
        queryset = models.OrderInfo.objects.filter(task_id=task_id, user_id=user_id)
        serializer = OrderInfoSerializer(queryset, many=True)
        return Response({"code": return_code.SUCCESS, 'data': serializer.data})