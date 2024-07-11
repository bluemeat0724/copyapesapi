"""
当用户发起patch请求时，请求体为{'code':'123'}。
django在接收到请求后，提取出code值，在models.RedeemCodes里进行查询，
如果不存在，返回错误。如果存在code，提取出表中其他字段status，value。
如果status=2，表示code已经使用，返回报错。
如果status=1表示code未使用，将status值改为2，将request.user.id值存入user_id。
同时，使用user_id在models.QuotaInfo里查询quota_0和quota_1，将value的值分别和quota_0、quota_1相加后保存
"""

from crawler.updata_ip_countdown.ip_countdown import get_token
from api import models
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from api.extension import return_code
import datetime
import requests
import secrets
import string
import json



class RedeemCodesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RedeemCodes
        fields = '__all__'

class RedeemCodesView(APIView):
    """兑换码核销"""

    def patch(self, request):
        # 获取请求体中的code值
        serializer = RedeemCodesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data.get('code')

        # 在 RedeemCodes 模型中查询 code
        try:
            redeem_code = models.RedeemCodes.objects.get(code=code)
        except models.RedeemCodes.DoesNotExist:
            return Response({"code": return_code.REDEEM_CODE_ERROR, 'detail': "兑换码不存在！"})

        # 检查 code 是否已经使用
        if redeem_code.status == 2:
            return Response({"code": return_code.REDEEM_CODE_ERROR, 'detail': "兑换码已使用！"})

        # 更新 RedeemCodes 模型中的状态和用户ID
        user_id = request.user.id
        redeem_code.status = 2
        redeem_code.user_id = user_id
        redeem_code.save()

        # 非首次购买，需要续期（countdown>0）
        token = get_token()
        ip_obj = models.IpInfo.objects.filter(user_id=user_id).first()
        if ip_obj:
            # 续期
            ip = ip_obj.ip
            countdown = ip_obj.countdown
            if countdown > 0:
                if renew_ip(token, ip):
                    return Response({"code": return_code.SUCCESS, 'detail': "IP续费成功！"})
                else:
                    return Response({"code": return_code.REDEEM_CODE_ERROR, 'detail': "IP续费失败！请联系客服处理！"})

        # 登录蜘蛛ip购买ip，同时修改子账号账号和密码
        ip_id, ip = buy_ip(token)
        # print("ip_id:", ip_id, "ip:", ip, "token:", token)
        if not ip:
            return Response({"code": return_code.REDEEM_CODE_ERROR, 'detail': "兑换IP失败！请联系客服处理！"})

        username = change_username(ip_id, token)
        if not username:
            return Response({"code": return_code.REDEEM_CODE_ERROR, 'detail': "兑换IP失败！请联系客服处理！"})

        # 首次购买写进IP表
        ip_obj, created = models.IpInfo.objects.get_or_create(user_id=user_id,defaults={
                'ip': ip,
                'username': username,
                'password': '12345678',
                'countryName': '中国台湾省',
                'countdown': 30,
                'stop_day': 0.5,
                'tips_day': 3,
                'created_at': datetime.datetime.now(),
                'experience_day': 0
            })
        # 非首次购买，旧IP不在有效期
        if not created:
            ip_obj.ip = ip
            ip_obj.username = username
            ip_obj.password = '12345678'
            ip_obj.countryName = '中国台湾省'
            ip_obj.countdown = 30
            ip_obj.stop_day = 0.5
            ip_obj.tips_day = 3
            ip_obj.created_at = datetime.datetime.now()
            ip_obj.experience_day = 0
            ip_obj.save()
        return Response({"code": return_code.SUCCESS, 'detail': "兑换IP成功！"})



def buy_ip(token):
    url = "https://www.zhizhuip.cc/externalapi/product_order/createProductOrder"
    payload = {
        'access_token': token,
        'type': 2,
        'status': 1,
        'conpon_id': 0,
        'num': 1,
        'country': 'TW',
        'timelen': 1,
        'agree': 'SOCKS5',
        'city': 'Taipei',
        'use_random_username': 0
    }
    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)'
    }

    res = requests.post(url, data=payload, headers=headers).json().get('data').get('subAccounts')[0]
    ip_id = res.get('id')
    ip = res.get('ip')
    return ip_id, ip

def change_username(ip_id, token):
    characters = string.ascii_letters + string.digits
    username = ''.join(secrets.choice(characters) for _ in range(8))

    url = "https://www.zhizhuip.cc/externalapi/device/batchUpdateSubAccountUsernamePassword"
    payload = {
        'access_token': token,
        'type': 2,
        'status': 1,
        'content[0][id]': ip_id,
        'content[0][customUsername]': username,
        'content[0][customPassword]': '12345678',
    }
    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)'
    }

    res = requests.put(url, data=payload, headers=headers).json()
    if res.get('code') == 1:
        return username
    else:
        return False

def renew_ip(token, ip):
    ip_id, country = get_ip_id(token, ip)
    url = "https://www.zhizhuip.cc/externalapi/set_meal/renewOrder"
    payload = {
        'access_token': token,
        'type': 2,
        'status': 1,
        'conpon_id': '',
        'content': [
            {
                'country': country,
                'ids': [int(ip_id)],
                'timelen': 1
            }
        ]
    }
    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Content-Type': 'application/json'
    }

    res = requests.post(url, json=payload, headers=headers).json()
    if res.get('code') == 1:
        return True
    else:
        return False

def get_ip_id(token,ip):
    url = "https://www.zhizhuip.cc/externalapi/device/accountList"
    params = {
        'access_token': token,
        'type': '2',
        'status': '1',
        'page': '1',
        'pagesize': '500'
    }
    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)'
    }

    response = requests.get(url, params=params, headers=headers)
    data = json.loads(response.text)
    ip_list = data.get('data', {}).get('rows', [])
    for i in ip_list:
        if i.get('ip') == ip:
            return i.get('id'), i.get('country')
