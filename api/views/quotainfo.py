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
        # ip = get_client_ip(request)
        user_id = request.user.id
        queryset = models.QuotaInfo.objects.filter(user_id=user_id)
        serializer = QuotaInfoSerializer(queryset, many=True)
        return Response({"code": return_code.SUCCESS, 'data': serializer.data})

# def get_client_ip(request):
#     x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#     if x_forwarded_for:
#         ip = x_forwarded_for.split(',')[0]
#     else:
#         ip = request.META.get('REMOTE_ADDR')
#     return ip