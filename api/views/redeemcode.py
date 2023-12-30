"""
当用户发起patch请求时，请求体为{'code':'123'}。
django在接收到请求后，提取出code值，在models.RedeemCodes里进行查询，
如果不存在，返回错误。如果存在code，提取出表中其他字段status，value。
如果status=2，表示code已经使用，返回报错。
如果status=1表示code未使用，将status值改为2，将request.user.id值存入user_id。
同时，使用user_id在models.QuotaInfo里查询quota_0和quota_1，将value的值分别和quota_0、quota_1相加后保存
"""


from api import models
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from api.extension import return_code
import datetime



class RedeemCodesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RedeemCodes
        fields = '__all__'

class RedeemCodesView(APIView):
    """兑换码核销"""

    def patch(self, request):
        # 获取请求体中的code值
        serializer = RedeemCodesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data.get('code')

        # 在 RedeemCodes 模型中查询 code
        try:
            redeem_code = models.RedeemCodes.objects.get(code=code)
        except models.RedeemCodes.DoesNotExist:
            return Response({"code": return_code.REDEEM_CODE_ERROR, 'detail': "兑换码不存在！"})

        # 检查 code 是否已经使用
        if redeem_code.status == 2:
            return Response({"code": return_code.REDEEM_CODE_ERROR, 'detail': "兑换码已使用！"})

        # 更新 RedeemCodes 模型中的状态和用户ID
        redeem_code.status = 2
        redeem_code.user_id = request.user.id
        redeem_code.save()

        # 在 QuotaInfo 模型中查询对应用户的配额信息
        try:
            quota_info = models.QuotaInfo.objects.get(user_id=request.user.id)
        except models.QuotaInfo.DoesNotExist:
            return Response({"code": return_code.PERMISSION_DENIED, 'detail': "账户受限，请联系客服！"})

        # 更新配额信息
        quota_info.quota_0 += redeem_code.value
        quota_info.quota_1 += redeem_code.value
        quota_info.verification_datetime = datetime.datetime.now()
        quota_info.save()

        return Response({"code": return_code.SUCCESS, 'detail': "充值成功！"})

