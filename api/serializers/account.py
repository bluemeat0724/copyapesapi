from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from api import models


class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(label="确认密码", min_length=6, write_only=True)
    password = serializers.CharField(label="密码", min_length=6, write_only=True)

    class Meta:
        model = models.UserInfo
        fields = ['username', "password", "confirm_password"]

    def validate_username(self, value):
        exists = models.UserInfo.objects.filter(username=value).exists()
        if exists:
            raise ValidationError("用户名已存在")
        return value

    def validate_confirm_password(self, value):
        password = self.initial_data.get('password')
        if password == value:
            return value
        raise ValidationError("两次密码不一致")


class AuthSerializer(serializers.Serializer):
    username = serializers.CharField(label="用户名", write_only=True, required=False)
    password = serializers.CharField(label="密码", min_length=6, write_only=True)

