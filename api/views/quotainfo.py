from api import models
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from api.extension import return_code

class QuotaInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.QuotaInfo
        fields = '__all__'

class QuotaView(APIView):
    """用户收益和可用额度"""

    def get(self, request):
        user_id = request.user.id
        queryset = models.QuotaInfo.objects.filter(user_id=user_id)
        serializer = QuotaInfoSerializer(queryset, many=True)
        return Response({"code": return_code.SUCCESS, 'data': serializer.data})