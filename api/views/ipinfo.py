from api.extension.filter import SelfFilterBackend
from api.extension.mixins import CopyListModelMixin, CopyCreateModelMixin, CopyUpdateModelMixin
from api import models
from api.serializers.ipinfo import IpSerializer


class IpView(CopyListModelMixin, CopyCreateModelMixin, CopyUpdateModelMixin):
    """IP"""
    # 当前登录用户筛选
    filter_backends = [SelfFilterBackend]

    serializer_class = IpSerializer
    queryset = models.IpInfo.objects.filter(countdown__gt=0)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


