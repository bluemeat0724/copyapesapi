from crawler.utils.get_proxies import get_my_proxies
from crawler.utils.db import Connect

def api(user_id, api_id):
    with Connect() as conn:
        api_dict = conn.fetch_one("select flag,passPhrase,api_key,secret_key from api_apiinfo where id=%(id)s",
                                  id={api_id})
    flag = str(api_dict.get('flag'))
    acc = {
        'key': str(api_dict.get('api_key')),
        'secret': str(api_dict.get('secret_key')),
        'passphrase': str(api_dict.get('passPhrase')),
        'proxies': get_my_proxies(user_id, flag)
    }
    return acc, flag


if __name__ == '__main__':
    print(api(1, 2))