from rest_framework import serializers
from api import models


class IpSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.IpInfo
        fields = '__all__'