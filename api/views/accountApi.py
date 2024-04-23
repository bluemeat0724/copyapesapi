from api.extension.filter import SelfFilterBackend
from api.extension.mixins import CopyCreateModelMixin, CopyListModelMixin, CopyDestroyModelMixin, CopyUpdateModelMixin
from api.serializers.accountApi import ApiSerializer
from api import models
from rest_framework.response import Response
from api.extension import return_code
from crawler.myokx import app
from crawler.utils.get_proxies import get_my_proxies
import re


class ApiAddView(CopyCreateModelMixin, CopyListModelMixin, CopyDestroyModelMixin, CopyUpdateModelMixin):
    """用户API提交"""
    # 当前登录用户筛选
    filter_backends = [SelfFilterBackend]

    serializer_class = ApiSerializer
    queryset = models.ApiInfo.objects.filter(deleted=False).order_by('-id')

    # 禁止重复添加
    def create(self, request, *args, **kwargs):
        # 从请求中获取api_key和secret_key
        user_id = request.user.id
        platform = request.data.get('platform')
        flag = request.data.get('flag')
        if platform == '1':
            passPhrase = request.data.get('passPhrase')
        api_key = request.data.get('api_key')
        secret_key = request.data.get('secret_key')

        # 检查是否存在相同的api_key和secret_key，且未被删除
        if models.ApiInfo.objects.filter(api_key=api_key, secret_key=secret_key, deleted=False).exists():
            # 如果存在，返回错误响应
            return Response({
                'code': return_code.EXIST_ERROR,
                'error': 'API信息已存在，不能重复添加'})

        # 交易所验证api
        if platform == '1':
            if flag == '1':
                acc = {
                    'passphrase': passPhrase,
                    'key': api_key,
                    'secret': secret_key
                }
            elif flag == '0':
                proxies, ip_id = get_my_proxies(user_id, flag)
                if not proxies:
                    return Response({
                        'code': return_code.PROXY_ERROR,
                        'error': '没有添加代理IP，无法绑定实盘API'})
                acc = {
                    'passphrase': passPhrase,
                    'key': api_key,
                    'secret': secret_key,
                    'proxies': proxies
                }
            try:
                obj = app.OkxSWAP(**acc)
                obj.account.api.flag = str(flag)
                obj.trade.api.flag = str(flag)
                # 账户层级
                acctLv = obj.account.get_config().get('data')[0].get('acctLv')
                if acctLv == '1':
                    return Response({
                        'code': return_code.API_ERROR,
                        'error': '当前API无法进行合约交易，请在交易所合约交易页面手动设置！'})
                # uid
                uid = obj.account.get_config().get('data')[0].get('uid')
                if models.ApiInfo.objects.filter(uid=uid, deleted=False).exists():
                    return Response({
                        'code': return_code.EXIST_ERROR,
                        'error': '当前交易所账户已授权，请勿重复绑定！可在交易所申请子账户继续绑定！'})

                # ip白名单
                ip = obj.account.get_config().get('data')[0].get('ip')
                # 用户角色
                roleType = obj.account.get_config().get('data')[0].get('roleType')
                # 用户等级
                level = obj.account.get_config().get('data')[0].get('level')
                # api权限
                perm = obj.account.get_config().get('data')[0].get('perm')

            except Exception as e:
                match = re.search(r'"code":"(\d+)"', str(e))
                if match:
                    code_value = match.group(1)
                    if code_value == '50105':
                        return Response({
                            'code': return_code.API_ERROR,
                            'error': 'PASSPHRASE错误，请检查！'})
                return Response({
                    'code': return_code.API_ERROR,
                    'error': 'API信息错误，请检查！'})

        # 更新kwargs以包含新获取的信息
        request.data.update({
            'acctLv': acctLv,
            'ip': ip,
            'roleType': roleType,
            'level': level,
            'perm': perm,
            'uid': uid
        })

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
