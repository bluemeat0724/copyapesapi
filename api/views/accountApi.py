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

    # 禁止重复添加
    def create(self, request, *args, **kwargs):
        # 从请求中获取api_key和secret_key
        api_key = request.data.get('api_key')
        secret_key = request.data.get('secret_key')
        # 查看



        # 检查是否存在相同的api_key和secret_key，且未被删除
        if models.ApiInfo.objects.filter(api_key=api_key, secret_key=secret_key, deleted=False).exists():
            # 如果存在，返回错误响应
            return Response({
                'code': return_code.EXIST_ERROR,
                'error': 'API信息已存在，不能重复添加'})

        # 如果不存在，调用父类方法正常创建
        return super().create(request, *args, **kwargs)


    def perform_create(self, serializer):
        # flag = serializer.validated_data.get('flag')
        # if flag == 1:
        #     api_object = models.ApiInfo.objects.filter(flag=1, user=self.request.user, deleted=0).first()
        #     if not api_object:
        #         serializer.save(user=self.request.user)
        #     else:
        #         return Response({"code": return_code.FLAG_1_ERROR, "error": "每个用户只能保存一个模拟盘API"})
        serializer.save(user=self.request.user)


    def perform_destroy(self, instance):
        instance.deleted = True
        instance.save()
