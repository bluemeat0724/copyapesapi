from api.extension.mixins import CopyCreateModelMixin
from api.serializers.account import RegisterSerializer, AuthSerializer

from rest_framework.views import APIView
from rest_framework.response import Response

import uuid
import datetime
from django.db.models import Q

from api import models
from api.extension import return_code


class RegisterView(CopyCreateModelMixin):
    """用户注册"""
    authentication_classes = []
    permission_classes = []
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        serializer.validated_data.pop('confirm_password')
        serializer.save()


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
