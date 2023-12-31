from api.extension.filter import SelfFilterBackend
from api.extension.mixins import CopyCreateModelMixin, CopyListModelMixin, CopyDestroyModelMixin, CopyUpdateModelMixin
from api.serializers.accountApi import ApiSerializer
from api import models
from rest_framework.response import Response
from api.extension import return_code


class ApiAddView(CopyCreateModelMixin, CopyListModelMixin, CopyDestroyModelMixin, CopyUpdateModelMixin):
    """用户API提交"""
    # 当前登录用户筛选
    filter_backends = [SelfFilterBackend]

    serializer_class = ApiSerializer
    queryset = models.ApiInfo.objects.filter(deleted=False).order_by('-id')

    def perform_create(self, serializer):
        flag = serializer.validated_data.get('flag')
        if flag == 1:
            api_object = models.ApiInfo.objects.filter(flag=1, user=self.request.user, deleted=0).first()
            if not api_object:
                serializer.save(user=self.request.user)
            else:
                return Response({"code": return_code.FLAG_1_ERROR, "error": "每个用户只能保存一个模拟盘API"})
        serializer.save(user=self.request.user)


    def perform_destroy(self, instance):
        instance.deleted = True
        instance.save()
