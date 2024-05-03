import requests
from crawler.utils.get_header import get_header
from crawler.utils.get_proxies import get_proxies


url = 'https://www.binance.com/bapi/futures/v1/friendly/future/copy-trade/lead-portfolio/trade-history'
parser = {'pageNumber': 1, 'pageSize': 10, 'portfolioId': "3604350427900659457"}
# headers = {
#     'Accept': 'application/json, text/plain, */*',
#     'Accept-Encoding': 'gzip, deflate, br',
#     'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
#     'Connection': 'keep-alive',
#     'Content-Type': 'application/json',
#     'Origin': 'https://www.binance.com',
#     'Referer': 'https://www.binance.com/zh-CN/copy-trading/lead-details/3604350427900659457?timeRange=7D',
#     'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
#     'user-agent': 'Mozilla/5.0 (Windows NT 6.3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
# }
headers = get_header()
print(headers)

res = requests.post(url, headers=headers, json=parser)
print(res.text)