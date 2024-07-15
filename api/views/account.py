from api.extension.mixins import CopyCreateModelMixin
from api.serializers.account import RegisterSerializer, AuthSerializer, ChangeSerializer

from rest_framework.views import APIView
from rest_framework.response import Response

import uuid
import datetime
from django.db.models import Q

from api import models
from api.extension import return_code
from crawler.utils.db import Connect


def create_quota_info(user_id):
    """
    创建用户的QuotaInfo实例
    没有使用ORM，在此处进行手动余额初始化操作
    """
    params = {
        "user_id": user_id,
        "pnl_0": 0,
        "pnl_1": 0,
        "upl_0": 0,
        "upl_1": 0,
        "quota_0": 100,
        "quota_1": 100,
    }
    insert_sql = """
                    INSERT INTO api_quotainfo (user_id,pnl_0,pnl_1,upl_0,upl_1,quota_0,quota_1)
                    VALUES (%(user_id)s,%(pnl_0)s,%(pnl_1)s,%(upl_0)s,%(upl_1)s,%(quota_0)s,%(quota_1)s)
                """
    with Connect() as db:
        db.exec(insert_sql, **params)



class RegisterView(CopyCreateModelMixin):
    """用户注册"""
    authentication_classes = []
    permission_classes = []
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        serializer.validated_data.pop('confirm_password')
        # 保存用户信息
        user_instance = serializer.save()

        # 创建关联的QuotaInfo实例
        create_quota_info(user_instance.id)


class Login(APIView):
    """ 用户登录 """
    authentication_classes = []
    permission_classes = []

    # 2. 数据库校验用户名和密码的合法性
    def post(self, request):
        # 1. 获取用户请求 & 校验
        serializer = AuthSerializer(data=request.data)
        if not serializer.is_valid():
            # { 'username':[错误信息,], 'phone':[xxxx,]}
            return Response({"code": return_code.VALIDATE_ERROR, 'detail': serializer.errors})

        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')

        user_object = models.UserInfo.objects.filter(Q(username=username),
                                                     password=password).first()

        if not user_object:
            return Response({"code": return_code.VALIDATE_ERROR, "error": "用户名或密码错误"})

        token = str(uuid.uuid4())
        user_object.token = token
        # 设置token有效期：当前时间 + 2周
        user_object.token_expiry_date = datetime.datetime.now() + datetime.timedelta(weeks=2)
        user_object.save()

        return Response({"code": return_code.SUCCESS, "data": {"token": token, "name": user_object.username}})

    def get(self, request):
        """ 获取当前登录用户信息 """
        token = request.query_params.get("token")
        if not token:
            return Response({"code": return_code.VALIDATE_ERROR, "error": "用户未登录"})
        user_object = models.UserInfo.objects.filter(token=token).first()
        username = user_object.username
        return Response({"code": return_code.SUCCESS, "data": {"username": username}})

class ChangePassword(APIView):
    """ 修改密码 """

    def post(self, request):
        # 1. 获取用户请求 & 校验
        serializer = ChangeSerializer(data=request.data)
        if not serializer.is_valid():
            # { 'username':[错误信息,], 'phone':[xxxx,]}
            return Response({"code": return_code.VALIDATE_ERROR, 'detail': serializer.errors})

        # 获取当前登录用户
        user = request.user
        old_password = user.password

        password = serializer.validated_data.get('password')
        new_password = serializer.validated_data.get('new_password')
        confirm_password = serializer.validated_data.get('confirm_password')

        if len(new_password) < 6 and len(confirm_password) < 6:
            return Response({"code": return_code.VALIDATE_ERROR, "error": "密码长度不能小于6位"})
        if new_password != confirm_password:
            return Response({"code": return_code.VALIDATE_ERROR, "error": "两次密码输入不一致"})
        if new_password == old_password:
            return Response({"code": return_code.VALIDATE_ERROR, "error": "新密码不能与当前密码相同"})

        if old_password != password:
            return Response({"code": return_code.VALIDATE_ERROR, "error": "当前密码错误"})

        user.password = new_password
        user.save()
        return Response({"code": return_code.SUCCESS, "message": "密码修改成功"})