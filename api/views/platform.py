from api.extension.mixins import CopyListModelMixin
from api import models
from rest_framework import serializers

class Serializer(serializers.ModelSerializer):
    class Meta:
        model = models.Platform
        fields = '__all__'

class PlatformView(CopyListModelMixin,):
    """支持的交易所列表"""
    authentication_classes = []
    permission_classes = []
    serializer_class = Serializer
    queryset = models.Platform.objects.filter(deleted=False).order_by('id')