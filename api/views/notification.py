from api import models
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from api.extension import return_code
import secrets
import string



class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Notification
        fields = '__all__'

class WxView(APIView):
    """微信服务号通知"""

    def patch(self, request):
        """功能开关"""
        # 获取请求体中的wx值
        user_id = request.user.id
        wx = request.data.get('wx')

        # 查询是否有代理ip，有ip的才支持给通知
        if not models.IpInfo.objects.filter(user_id=user_id).exists():
            return Response({"code": return_code.PROXY_ERROR, 'msg': '请先绑定代理IP后再开启服务！'})

        # 在 Notification 模型中查询是否已有该用户的记录
        notify, created = models.Notification.objects.get_or_create(user_id=user_id)
        notify.wx = wx
        notify.save()
        return Response({"code": return_code.SUCCESS, 'wx': wx})

    def post(self, request):
        """创建/更新授权码"""

        def generate_code(length=12):
            characters = string.ascii_letters + string.digits
            code = 'ape-' + ''.join(secrets.choice(characters) for _ in range(length))
            return code

        user_id = request.user.id

        notify, created = models.Notification.objects.get_or_create(user_id=user_id)
        wx_code = generate_code()
        notify.wx_code = wx_code
        notify.wx = True
        notify.save()

        return Response({"code": return_code.SUCCESS, 'wx_code': wx_code})

    def get(self, request):
        """获取用户的微信通知设置"""
        user_id = request.user.id

        try:
            notify = models.Notification.objects.get(user_id=user_id)
            wx_code = notify.wx_code
            wx = notify.wx
            return Response({"code": return_code.SUCCESS, 'wx_code': wx_code, 'wx': wx})
        except models.Notification.DoesNotExist:
            return Response({"code": return_code.REDEEM_CODE_ERROR, 'detail': "微信服务号通知未设置"})
