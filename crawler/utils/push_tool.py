from crawler.utils.db import Connect
import requests


def wx_push(user_id):
    with Connect() as conn:
        wx_obj = conn.fetch_one(
            "select wx,wx_code from api_notification where user_id=%(user_id)s",
            user_id={user_id})
    if not wx_obj:
        return
    wx = wx_obj.get('wx')
    wx_code = wx_obj.get('wx_code').split('-')[1]
    # print(wx, wx_code)
    return wx, wx_code

class Push:
    def __init__(self, user_id, time_now, instId, posSide, lever, order_info):
        self.user_id = user_id
        self.wx, self.wx_code = wx_push(user_id)
        self.time_now = time_now
        self.order_info = order_info
        self.instId = instId
        self.posSide = posSide
        self.lever = lever

    def push(self):
        try:
            if self.wx:
                push_url = 'http://wxapi.copyapes.com/api/send_wx_message'
                data = {
                    "auth_code": self.wx_code,
                    "template_id": "tiS1Yw0EuNSwF3vFwlUPCqeXpVPH6z4mnzUG6Q_9h0c",
                    "send_data":  {
                        "time3": {"value": f"{self.time_now.strftime('%Y-%m-%d %H:%M:%S')}"},
                        "thing4": {"value": f"{self.instId.split('-')[0]}_{self.posSide}_x{self.lever}"},
                        "thing13":{"value": f"{self.order_info}"}
                    }
                }
                res = requests.post(push_url, json=data)
                # if res.json().get('errmsg') == 'ok':
                #     print('推送成功')
        except Exception as e:
            print(e)



if __name__ == '__main__':
    s_code_value = 51000
    Push(1, '2021-09-01 09:00:00', 'BTC-USDT', 'long', 10, f'开仓失败(code:{s_code_value})').push()