import imaplib

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


class NotifyView(APIView):
    def get(self, request):
        """获取用户的消息通知设置"""
        user_id = request.user.id
        try:
            notify = models.Notification.objects.get(user_id=user_id)
            serializer = NotificationSerializer(notify)
            return Response({"code": return_code.SUCCESS, 'data': serializer.data})
        except models.Notification.DoesNotExist:
            return Response({"code": return_code.REDEEM_CODE_ERROR, 'detail': "消息通知未设置"})


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



class QqmailView(APIView):
    """QQ邮箱通知"""

    def patch(self, request):
        """功能开关"""
        # 获取请求体中的wx值
        user_id = request.user.id
        qq_mail = request.data.get('qq_mail')

        # 在 Notification 模型中查询是否已有该用户的记录
        notify, created = models.Notification.objects.get_or_create(user_id=user_id)
        notify.qq_mail = qq_mail
        notify.save()
        return Response({"code": return_code.SUCCESS, 'qq_mail': qq_mail})

    def post(self, request):
        """提交QQ邮箱"""
        def qqmail(qq, password):
            # QQ邮箱的SMTP服务器地址和端口号
            smtp_server = 'imap.qq.com'
            port = 993
            sender = qq+'@qq.com'
            mail = imaplib.IMAP4_SSL(smtp_server, port)
            # 登录到服务器
            try:
                mail.login(sender, password)
                return True
            except:
                return False

        user_id = request.user.id
        qq = request.data.get('qq')
        password = request.data.get('password')

        # 校验邮箱和密码
        if not qqmail(qq, password):
            return Response({"code": return_code.REDEEM_CODE_ERROR, 'error': "邮箱或邮箱授权码错误!"})

        notify, created = models.Notification.objects.get_or_create(user_id=user_id)
        notify.qq = qq
        notify.password = password
        notify.qq_mail = True
        notify.save()
        return Response({"code": return_code.SUCCESS, 'detail': '提交成功'})
