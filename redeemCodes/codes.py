import secrets
import string
from crawler.utils.db import Connect

def generate_redeem_code(length=12):
    """生成指定长度的兑换码"""
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

    for _ in range(num_codes_to_generate):
        redeem_code = generate_redeem_code()
        store_redeem_code(redeem_code, 100)
        print(f"{redeem_code}")