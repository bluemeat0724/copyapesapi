from api.extension.mixins import CopyCreateModelMixin, CopyListModelMixin, CopyDestroyModelMixin, CopyUpdateModelMixin
from api.serializers.task import TaskcSerializer
from api import models
from django.db.models import Q
from api.extension import return_code
from rest_framework.response import Response
from django_redis import get_redis_connection
from django.conf import settings
from api.extension.filter import SelfFilterBackend



class TaskAddView(CopyCreateModelMixin, CopyListModelMixin, CopyDestroyModelMixin, CopyUpdateModelMixin):
    """用户跟单任务提交"""
    # 当前登录用户筛选
    filter_backends = [SelfFilterBackend]

    serializer_class = TaskcSerializer
    queryset = models.TaskInfo.objects.filter(deleted=False).order_by('-id')

    def perform_create(self, serializer):
        # 调用了is_valid()后通过serializer.validated_data属性来获取已验证的数据
        # 一个api只能对应一个跟单任务
        api = serializer.validated_data.get('api')
        user_object = models.TaskInfo.objects.filter(Q(api=api) & Q(status=1)).first()

        if user_object:
            return Response({"code": return_code.VALIDATE_ERROR, "error": "api已使用"})

        ip_object = models.IpInfo.objects.filter(Q(user=self.request.user) & Q(countdown__gt=0)).first()
        api_object = models.ApiInfo.objects.filter(Q(user=self.request.user) & Q(id=api.id)).first()
        flag = api_object.flag
        if not ip_object and flag == 0:
            return Response({"code": return_code.VALIDATE_ERROR, "error": "实盘交易请配置固定IP"})

        # 写入mysql
        serializer.save(user=self.request.user)

        # 写入Redis队列
        conn = get_redis_connection("default")
        tid = serializer.data.get('id')
        conn.lpush(settings.QUEUE_TASK_NAME, tid)


    def perform_update(self, serializer):
        serializer.save()
        # 写入Redis队列{'id': 1, 'status': 2}
        # 结束当前任务全部交易
        conn = get_redis_connection("default")
        tid = serializer.data.get('id')
        conn.lpush(settings.QUEUE_TASK_NAME, tid)




    def perform_destroy(self, instance):
        instance.deleted = True
        instance.save()
