from crawler.utils.db import Connect
import requests

import imaplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr


def push_info(user_id):
    with Connect() as conn:
        push_obj = conn.fetch_one(
            "select * from api_notification where user_id=%(user_id)s",
            user_id={user_id})
    if not push_obj:
        return

    # 微信服务号
    wx = push_obj.get('wx')
    wx_code = push_obj.get('wx_code').split('-')[1]

    # qq邮箱
    qqmail = push_obj.get('qq_mail')
    sender = push_obj.get('qq') + '@qq.com'
    password = push_obj.get('password')

    push_dict = {
        'wx': wx,
        'wx_code': wx_code,
        'qqmail': qqmail,
        'sender': sender,
        'password': password
    }

    return push_dict



class Push:
    def __init__(self, user_id, task_id, time_now, instId, posSide, lever, order_info, **kwargs):
        self.user_id = user_id
        self.task_id = task_id
        self.time_now = time_now
        self.order_info = order_info
        self.instId = instId
        self.posSide = posSide
        self.lever = lever

        # 处理额外的参数
        for key, value in push_info(user_id).items():
            setattr(self, key, value)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def push(self):
        if self.wx:
            self.wx_push()
        if self.qqmail:
            self.qqmail_push()

    def wx_push(self):
        push_url = 'http://wxapi.aiyao.top/api/send_wx_message'
        data = {
            "auth_code": self.wx_code,
            "template_id": "tiS1Yw0EuNSwF3vFwlUPCvk39lxvtjiMpNGxnP462fk",
            "send_data": {
                "time3": {"value": f"{self.time_now.strftime('%Y-%m-%d %H:%M:%S')}"},
                # "time3": {"value": f"{self.time_now}"},
                "character_string5": {"value": f"{self.task_id}"},
                "thing4": {"value": f"{self.instId.split('-')[0]}_{self.posSide}_x{self.lever}"},
                "thing13": {"value": f"{self.order_info}"}
            }
        }
        try:
            res = requests.post(push_url, json=data)
            # print(res.text)
            # if res.json().get('errmsg') == 'ok':
            #     print('推送成功')
        except Exception as e:
            print(e)

    def qqmail_push(self):
        # QQ邮箱的SMTP服务器地址和端口号
        smtp_server = 'smtp.qq.com'
        port = 465
        # 发件人和收件人的邮箱地址
        sender_name = '跟单猿'
        receiver = sender = self.sender
        # 邮件的内容
        if '失败' in self.order_info:
            subject = '#' + str(self.task_id) + '#' + self.instId + self.subject
        else:
            subject = '#' + str(self.task_id) + '#' + self.subject
        body = self.body
        msg = MIMEMultipart()
        msg['From'] = formataddr((sender_name, sender))
        msg['To'] = receiver
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            # 连接到 SMTP 服务器
            server = smtplib.SMTP_SSL(smtp_server, port)
            # 登录到服务器
            server.login(sender, self.password)
            # 发送邮件
            server.sendmail(sender, [receiver], msg.as_string())
            # 删除发送记录
            self.del_qqmail()
        except Exception as e:
            print(f"邮件发送失败: {e}")
        finally:
            # 关闭与 SMTP 服务器的连接
            server.quit()

    def del_qqmail(self):
        # QQ邮箱的imap服务器地址和端口号
        smtp_server = 'imap.qq.com'
        port = 993
        mail = imaplib.IMAP4_SSL(smtp_server, port)
        mail.login(self.sender, self.password)

        # 选择发件箱（已发送邮件的文件夹）
        mail.select('Sent')

        # 搜索所有邮件
        result, data = mail.search(None, 'ALL')

        # 获取邮件ID列表
        email_ids = data[0].split()

        if email_ids:
            # 获取第一封邮件的ID
            first_email_id = email_ids[-1]
            # 标记邮件为删除状态
            mail.store(first_email_id, '+FLAGS', '\\Deleted')
            # 彻底删除标记为删除状态的邮件
            mail.expunge()

        # 关闭IMAP连接
        mail.logout()


if __name__ == '__main__':
    s_code_value = 51000
    Push(1, 666, '2021-09-01 09:00:00', 'BTC-USDT-SWAP', 'long', 10, f'开仓失败(code:{s_code_value})', subject='交易失败', body='当前IP不在你的API白名单内，请前往交易所API管理页面添加IP白名单！').push()
    # Push(1, 666, '2021-09-01 09:00:00', 'BTC-USDT-SWAP', 'long', 10, f'open', subject='进行开仓操作', body='品种：BTC-USDT-SWAP，金额：100.0USDT，方向：long').push()