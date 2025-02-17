from api.extension.mixins import CopyCreateModelMixin, CopyListModelMixin, CopyDestroyModelMixin, CopyUpdateModelMixin
from api.serializers.task import TaskSerializer
from api import models
from django.db.models import Q
from api.extension import return_code
from rest_framework.response import Response
from django_redis import get_redis_connection
from django.conf import settings
from api.extension.filter import SelfFilterBackend
from django.utils import timezone
from datetime import timedelta



class TaskAddView(CopyCreateModelMixin, CopyListModelMixin, CopyDestroyModelMixin, CopyUpdateModelMixin):
    """用户跟单任务提交"""
    # 当前登录用户筛选
    filter_backends = [SelfFilterBackend]

    serializer_class = TaskSerializer
    queryset = models.TaskInfo.objects.filter(deleted=False).order_by('-id')

    def perform_create(self, serializer):
        # 调用了is_valid()后通过serializer.validated_data属性来获取已验证的数据
        # 一个api只能对应一个跟单任务
        api = serializer.validated_data.get('api')
        user_object = models.TaskInfo.objects.filter(Q(api=api) & Q(status=1)).first()

        if user_object:
            return Response({"code": return_code.VALIDATE_ERROR, "error": "api已使用"})

        # 检查是否有绑定固定ip
        ip_object = models.IpInfo.objects.filter(Q(user=self.request.user) & Q(countdown__gt=0)).first()
        api_object = models.ApiInfo.objects.filter(Q(user=self.request.user) & Q(id=api.id)).first()
        flag = api_object.flag
        if not ip_object and flag == 0:
            return Response({"code": return_code.VALIDATE_ERROR, "error": "实盘交易请配置固定IP"})

        # 判断是否有固定ip且是否开跟单普通用户
        role_type = serializer.validated_data.get('role_type')
        if not ip_object and role_type == 2:
            return Response({"code": return_code.VALIDATE_ERROR, "error": "跟单普通用户请配置固定IP"})


        # 检查ip是否到期
        if ip_object:
            countdown = ip_object.countdown
            stop_day = ip_object.stop_day
            created_at = ip_object.created_at
            experience_day = ip_object.experience_day
            now = timezone.now()
            if countdown <= stop_day and experience_day == 0:
                return Response({"code": return_code.VALIDATE_ERROR, "error": "IP即将过期，无法创建任务"})
            if experience_day > 0 and created_at < now - timedelta(experience_day - stop_day):
                return Response({"code": return_code.VALIDATE_ERROR, "error": "IP即将过期，无法创建任务"})

        # 检查是否有正在进行中的任务
        if models.TaskInfo.objects.filter(Q(user=self.request.user) & Q(status=1)).exists():
            return Response({"code": return_code.VALIDATE_ERROR, "error": "已有任务在运行，由于访问频率限制，不支持同时开多个任务"})

        # 检查剩余可用额度
        # quota_object = models.QuotaInfo.objects.filter(Q(user=self.request.user)).first()
        # if flag == 0:
        #     quota = quota_object.quota_0
        # elif flag == 1:
        #     quota = quota_object.quota_1
        # sums = serializer.validated_data.get('sums')
        # if quota < sums:
        #     return Response({"code": return_code.VALIDATE_ERROR, "error": "可用额度不足！请充值额度，或减少跟单金额！"})

        # 写入mysql
        serializer.save(user=self.request.user)

        # 写入Redis队列
        conn = get_redis_connection("default")
        tid = serializer.data.get('id')
        conn.lpush(settings.QUEUE_TASK_NAME, tid)


    def perform_update(self, serializer):
        serializer.save()

        # 从请求体获取task_id，再获取api_id
        task_id = self.request.data.get('task_id')
        task_object = models.TaskInfo.objects.filter(Q(id=task_id)).first()
        api_id = task_object.api_id
        # 将api使用状态改为1，释放api
        api_object = models.ApiInfo.objects.filter(Q(id=api_id)).first()
        api_object.status = 1
        api_object.save()

        # 写入Redis队列{'id': 1, 'status': 2}

        # 结束当前任务全部交易
        conn = get_redis_connection("default")
        tid = serializer.data.get('id')
        conn.lpush(settings.QUEUE_TASK_NAME, tid)




    def perform_destroy(self, instance):
        instance.deleted = True
        instance.save()
