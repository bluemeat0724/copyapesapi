from api.extension import return_code
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


class CopyCreateModelMixin(mixins.CreateModelMixin, GenericViewSet):
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        # 1. 异常处理
        if not serializer.is_valid():
            return Response({"code": return_code.VALIDATE_ERROR, 'detail': serializer.errors})
        # 2. 优化perform_create
        res = self.perform_create(serializer)
        # 3. 返回数据的处理
        return res or Response({"code": return_code.SUCCESS, 'data': serializer.data})

class CopyListModelMixin(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response({"code": return_code.SUCCESS, 'data': serializer.data})

        serializer = self.get_serializer(queryset, many=True)
        return Response({"code": return_code.SUCCESS, 'data': serializer.data})


class CopyDestroyModelMixin(mixins.DestroyModelMixin, GenericViewSet):
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        res = self.perform_destroy(instance)
        return res or Response({"code": return_code.SUCCESS, 'data': '删除成功！'})


class CopyUpdateModelMixin(mixins.UpdateModelMixin, GenericViewSet):
    def destroy(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response({"code": return_code.VALIDATE_ERROR, 'detail': serializer.errors})
        res = self.perform_update(serializer)
        return res or Response({"code": return_code.SUCCESS, 'data': serializer.data})
