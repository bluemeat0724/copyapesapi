import json
import requests
from api.extension.filter import SelfFilterBackend
from api.extension.mixins import CopyListModelMixin, CopyCreateModelMixin, CopyUpdateModelMixin
from api import models
from api.serializers.ipinfo import IpSerializer
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from rest_framework.response import Response
from api.extension import return_code
from crawler.updata_ip_countdown.ip_countdown import get_token


class IpView(CopyListModelMixin, CopyCreateModelMixin, CopyUpdateModelMixin):
    """IP"""
    # 当前登录用户筛选
    filter_backends = [SelfFilterBackend]

    serializer_class = IpSerializer

    # 筛选有效期>0的ip
    # queryset = models.IpInfo.objects.filter(countdown__gt=0)
    # 构建查询条件：ip有效期>0, 或者试用有效期>0天（试用期days=15天）
    def get_queryset(self):
        now = timezone.now()
        # 构建查询条件
        conditions = (Q(countdown__gt=0) & Q(experience_day=0)) | (
                Q(experience_day__gt=0) &
                Q(created_at__gt=now - timedelta(days=15))
        )
        queryset = models.IpInfo.objects.filter(conditions)
        return queryset

    def perform_create(self, serializer):
        # 用户主动添加IP时，一个IP只能对应一个user_id
        ip = serializer.validated_data.get('ip')
        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')
        ip_obj = models.IpInfo.objects.filter(ip=ip, username=username, password=password).first()
        if ip_obj:
            return Response({"code": return_code.VALIDATE_ERROR, "error": "IP已被使用，需添加独享IP"})
        # 校验IP真实性
        countdown, countryName = self.check_ip(ip, username, password)
        if countdown is None:
            return Response({"code": return_code.VALIDATE_ERROR, "error": "IP不存在，请填写正确的IP信息！"})
        else:
            serializer.validated_data.update(countdown=countdown, countryName=countryName)

        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # 用户主动更新IP时，一个IP只能对应一个user_id
        ip = serializer.validated_data.get('ip')
        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')
        # 确保更新的IP不会违反唯一性约束
        ip_obj = models.IpInfo.objects.filter(ip=ip, username=username, password=password).exclude(
            id=instance.id).first()

        if ip_obj:
            return Response({"code": return_code.VALIDATE_ERROR, "error": "IP已被使用，需添加独享IP"})

        # 校验IP真实性
        countdown, countryName = self.check_ip(ip, username, password)
        if countdown is None:
            return Response({"code": return_code.VALIDATE_ERROR, "error": "IP不存在，请填写正确的IP信息！"})
        else:
            serializer.validated_data.update(countdown=countdown, countryName=countryName)

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response({"code": return_code.SUCCESS, "msg": "修改成功"})

    def check_ip(self, ip, username, password):
        """在线校验IP"""
        token = get_token()
        url = "https://www.zhizhuip.cc/externalapi/device/accountList"
        params = {
            'access_token': token,
            'type': '2',
            'status': '1',
            'page': '1',
            'pagesize': '500'
        }
        headers = {
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)'
        }

        response = requests.get(url, params=params, headers=headers)
        data = json.loads(response.text)
        ip_list = data.get('data', {}).get('rows', [])
        # print(ip_list)
        for i in ip_list:
            if i.get('ip') == ip and i.get('username') == username and i.get('password') == password:
                countdown = float(i.get('countdown').split('天')[0])
                countryName = i.get('countryName')
                return countdown,countryName
        return None, None
