import secrets
import string
from crawler.utils.db import Connect

def generate_redeem_code(length=12):
    """
    生成指定长度的兑换码
    $100     12位
    $300     13位
    $500     14位
    $1000    15位
    $5000    16位
    $10000   17位
    """
    characters = string.ascii_letters + string.digits
    redeem_code = ''.join(secrets.choice(characters) for _ in range(length))
    return redeem_code

def store_redeem_code(redeem_code, value):
     """将兑换码存储在数据库中"""
     insert_sql = """
                INSERT INTO api_redeemcodes (code, value, status)
                VALUES (%(code)s, %(value)s, 1)           
            """
     with Connect() as db:
         db.exec(insert_sql, **{'code': redeem_code, 'value': value})


if __name__ == "__main__":
    num_codes_to_generate = 1
    value = 1000

    for _ in range(num_codes_to_generate):
        redeem_code = generate_redeem_code()
        store_redeem_code(redeem_code, value)
        print(f"{redeem_code}")