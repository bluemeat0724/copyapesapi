from django.db import models

class DeletedModel(models.Model):
    deleted = models.BooleanField(verbose_name="已删除", default=False)

    class Meta:
        abstract = True


class UserInfo(models.Model):
    """ 用户表 """
    username = models.CharField(verbose_name="用户名", max_length=32, db_index=True)
    password = models.CharField(verbose_name="密码", max_length=64)

    token = models.CharField(verbose_name="token", max_length=64, null=True, blank=True, db_index=True)
    token_expiry_date = models.DateTimeField(verbose_name="token有效期", null=True, blank=True)

    status_choice = (
        (1, "激活"),
        (2, "禁用"),
    )
    status = models.IntegerField(verbose_name="状态", choices=status_choice, default=1)
    create_datetime = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['username', "password"], name='idx_name_pwd')
        ]

class Platform(DeletedModel):
    """交易所表"""
    platform = models.CharField(verbose_name="交易所", max_length=32, db_index=True)


class ApiInfo(DeletedModel):
    """交易所API表"""
    platform_choice = (
        (1, "okx"),
    )
    platform = models.IntegerField(verbose_name="交易所", choices=platform_choice, default=1)
    create_datetime = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    api_name = models.CharField(verbose_name="api备注名", max_length=32, db_index=True)

    flag_choice = (
        (0, "实盘"),
        (1, "模拟盘")
    )
    flag = models.IntegerField(verbose_name="API类型", choices=flag_choice, default=0)
    passPhrase = models.CharField(verbose_name="密码", max_length=64)
    api_key = models.CharField(verbose_name="APIKEY", max_length=64)
    secret_key = models.CharField(verbose_name="SECRETKEY", max_length=64)

    status_choice = (
        (1, "空闲"),
        (2, "使用中"),
    )
    status = models.IntegerField(verbose_name="状态", choices=status_choice, default=1)
    user = models.ForeignKey(verbose_name="用户", to="UserInfo", on_delete=models.CASCADE)
    """用户API资产"""
    usdt = models.FloatField(verbose_name="usdt", default=0)
    btc = models.FloatField(verbose_name="btc", default=0)
    eth = models.FloatField(verbose_name="eth", default=0)
    """api收益，通过api关联任务收益累加"""
    pnl = models.FloatField(verbose_name="已实现跟单收益", default=0)
    upl = models.FloatField(verbose_name="未实现跟单收益", default=0)
    """API交易所账号信息补全"""
    acctLv = models.CharField(verbose_name="账户等级", max_length=8, null=True, blank=True)
    ip = models.CharField(verbose_name="ip", max_length=128, null=True, blank=True)
    roleType = models.CharField(verbose_name="角色", max_length=8, null=True, blank=True)
    level = models.CharField(verbose_name="等级", max_length=8, null=True, blank=True)
    perm = models.CharField(verbose_name="权限", max_length=32, null=True, blank=True)
    uid = models.CharField(verbose_name="uid", max_length=32, null=True, blank=True)


class TaskInfo(DeletedModel):
    platform_choice = (
        (1, "okx"),
    )
    trader_platform = models.IntegerField(verbose_name="交易所", choices=platform_choice, default=1)
    uniqueName = models.CharField(verbose_name="交易员交易所ID", max_length=32)

    api = models.ForeignKey(verbose_name="api", to="ApiInfo", on_delete=models.CASCADE)
    role_choice = (
        (1, "带单员"),
        (2, "普通用户"),
    )
    role_type = models.IntegerField(verbose_name="交易员类型", choices=role_choice, default=1)
    reduce_ratio = models.FloatField(verbose_name="减仓比例", default=0.0)

    follow_choice = (
        (1, "固定金额"),
        (2, "固定比例"),
    )
    follow_type = models.IntegerField(verbose_name="跟单模式", choices=follow_choice, default=1)
    sums = models.FloatField(verbose_name="单笔跟单金额", default=0.0)
    ratio = models.FloatField(verbose_name="跟单比例", default=0.0)
    lever_choice = (
        (1, "跟随交易员"),
        (2, "自定义杠杆"),
    )
    lever_set = models.IntegerField(verbose_name="杠杆设置", choices=lever_choice, default=1)

    leverage = models.IntegerField(
        verbose_name="杠杆倍数",
        default=1  # 默认值
    )

    investment = models.FloatField(verbose_name="投资金额", default=0)

    posSide_set = models.IntegerField(
        verbose_name="反向跟单",
        default=1  # 默认值 1：否 2：是
    )

    first_order_choice = (
        (1, "交易员新开订单后跟随"),
    )
    first_order_set = models.IntegerField(verbose_name="首单跟单设置", choices=first_order_choice, default=1)

    status_choice = (
        (1, "跟单进行中"),
        (2, "跟单结束"),
        (3, "自动结束"),
    )
    status = models.IntegerField(verbose_name="状态", choices=status_choice, default=1)
    user = models.ForeignKey(verbose_name="用户", to="UserInfo", on_delete=models.CASCADE)
    create_datetime = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    pnl = models.FloatField(verbose_name="已实现跟单收益", default=0)
    ip_id = models.IntegerField(verbose_name="ip的id", null=True)
    fast_mode_choice = (
        (0, "否"),
        (1, "是"),
    )
    fast_mode = models.IntegerField(verbose_name="是否极速", choices=fast_mode_choice, default=0)

    """是否开启单笔止盈止损"""
    trade_trigger_mode_choice = (
        (0, "否"),
        (1, "是"),
    )
    trade_trigger_mode = models.IntegerField(verbose_name="是否开启单笔止盈止损", choices=trade_trigger_mode_choice, default=0)
    sl_trigger_px = models.FloatField(verbose_name="止损触发比例", default=0, null=True, blank=True)
    tp_trigger_px = models.FloatField(verbose_name="止盈触发比例", default=0, null=True, blank=True)

    """开仓模式"""
    first_open_type_choice = (
        (1, "当前市价"),
        (2, "区间限价"),
    )
    first_open_type = models.IntegerField(verbose_name="开仓模式", choices=first_open_type_choice, default=1)
    uplRatio = models.FloatField(verbose_name="交易员当前收益率", default=0)


class IpInfo(models.Model):
    """IP代理"""
    ip = models.GenericIPAddressField(verbose_name="IP地址")
    username = models.CharField(verbose_name="代理用户名", max_length=32, db_index=True)
    password = models.CharField(verbose_name="代理密码", max_length=64)
    countryName = models.CharField(verbose_name="地区", max_length=32, null=True, blank=True, default='')
    countdown = models.FloatField(verbose_name="有效期", default=30)
    user = models.ForeignKey(verbose_name="用户", to="UserInfo", on_delete=models.CASCADE)
    stop_day = models.FloatField(verbose_name="停止交易时间", default=0.5)
    tips_day = models.FloatField(verbose_name="提示ip过期时间", default=3)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    experience_day = models.FloatField(verbose_name="有效天数", default=0)


class OrderInfo(models.Model):
    """交易记录"""
    user = models.ForeignKey(verbose_name="用户", to="UserInfo", on_delete=models.CASCADE, db_index=True)
    task = models.ForeignKey(verbose_name="任务", to="TaskInfo", on_delete=models.CASCADE, db_index=True)
    api = models.ForeignKey(verbose_name="api", to="ApiInfo", on_delete=models.CASCADE)
    status_choice = (
        (1, "进行中"),
        (2, "结束"),
    )
    status = models.IntegerField(verbose_name="交易状态", choices=status_choice, default=1)
    instId = models.CharField(verbose_name="交易品种", max_length=32)
    cTime = models.BigIntegerField(verbose_name="开仓时间", default=int)
    uTime = models.BigIntegerField(verbose_name="平仓时间", default=int, null=True, blank=True)
    openAvgPx = models.FloatField(verbose_name="开仓均价", default=0)
    closeAvgPx = models.FloatField(verbose_name="平仓均价", default=0, null=True, blank=True)
    pnl = models.FloatField(verbose_name="已实现收益", default=0)
    pnlRatio = models.FloatField(verbose_name="收益率", default=0)
    upl = models.FloatField(verbose_name="未实现收益", default=0)
    uplRatio = models.FloatField(verbose_name="未实现收益率", default=0)
    lever = models.CharField(verbose_name="杠杆", max_length=6, default="0")
    mgnMode = models.CharField(verbose_name="保证金模式", max_length=10, default="cross")
    posSide = models.CharField(verbose_name="持仓方向", max_length=10)
    imr = models.FloatField(verbose_name="保证金", default=0)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'task'], name='idx_user_task'),
        ]


class QuotaInfo(models.Model):
    """盈利和剩余可兑盈利额度"""
    user = models.ForeignKey(verbose_name="用户", to="UserInfo", on_delete=models.CASCADE, db_index=True)
    pnl_0 = models.FloatField(verbose_name="实盘累计收益", default=0)
    upl_0 = models.FloatField(verbose_name="实盘未实现收益", default=0)
    pnl_1 = models.FloatField(verbose_name="模拟盘累计收益", default=0)
    upl_1 = models.FloatField(verbose_name="模拟盘未实现收益", default=0)
    quota_0 = models.FloatField(verbose_name="实盘剩余盈利额度", default=100)
    quota_1 = models.FloatField(verbose_name="模拟盘剩余盈利额度", default=100)


class RedeemCodes(models.Model):
    """兑换码"""
    user = models.ForeignKey(verbose_name="用户", to="UserInfo", on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    code = models.CharField(verbose_name="兑换码", max_length=64, db_index=True)
    status_choice = (
        (1, "未使用"),
        (2, "已使用"),
    )
    status = models.IntegerField(verbose_name="可用状态", choices=status_choice, default=1)
    value = models.FloatField(verbose_name="兑换金额", default=0)
    verification_datetime = models.DateTimeField(verbose_name="兑换码验证时间", null=True, blank=True, auto_now=True)


class SpiderLog(models.Model):
    """爬虫日志"""
    user_id = models.IntegerField(verbose_name="用户ID", db_index=True)
    task_id = models.IntegerField(verbose_name="任务ID", db_index=True)
    date = models.DateTimeField(verbose_name="日志时间戳")
    color = models.CharField(verbose_name="日志级别", max_length=255)
    title = models.CharField(verbose_name="标题", max_length=255)
    description = models.TextField(verbose_name="日志信息")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        verbose_name = "爬虫日志"
        verbose_name_plural = "爬虫日志"


class TradeLog(models.Model):
    """交易日志"""
    user_id = models.IntegerField(verbose_name="用户ID", db_index=True)
    task_id = models.IntegerField(verbose_name="任务ID", db_index=True)
    date = models.DateTimeField(verbose_name="日志时间戳")
    color = models.CharField(verbose_name="日志级别", max_length=255)
    title = models.CharField(verbose_name="标题", max_length=255)
    description = models.TextField(verbose_name="日志信息")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        verbose_name = "交易日志"
        verbose_name_plural = "交易日志"