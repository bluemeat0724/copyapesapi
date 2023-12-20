from django.urls import path
from rest_framework import routers
from api.views import account, accountApi, task, platform, ipinfo, tradedetial, tradeorder, quotainfo, redeemcode

router = routers.SimpleRouter()
router.register(r'register', account.RegisterView, 'register')
router.register(r'apiadd', accountApi.ApiAddView, 'apiadd')
router.register(r'taskadd', task.TaskAddView, 'taskadd')
router.register(r'platform', platform.PlatformView, 'platform')
router.register(r'ip', ipinfo.IpView, 'ip')

urlpatterns = [
    # path('register/', account.RegisterView.as_view({"post": "create"})),
    path('login/', account.Login.as_view()),
    path('traderdetial/<int:task_id>/', tradedetial.TradeDetailView.as_view()),
    path('tradeorder/<int:task_id>/', tradeorder.OrderView.as_view()),
    path('quotainfo/', quotainfo.QuotaView.as_view()),
    path('redeemcode/', redeemcode.RedeemCodesView.as_view()),
]

urlpatterns += router.urls
