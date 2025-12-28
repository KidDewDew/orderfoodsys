
'''全局变量'''
import datetime
import random
from flask import session

# 数据库连接(mysql.connection)
db_connection = {}
# 两个字符串
RANDOM_STR_vc = "23456789abcdefghjkmnpqrstuwxyz" # 验证码字符，排除了0、o、I、l等容易让用户分不清的字符对。
RANDOM_STR_1 = "abcdefghijklmnopqrstuvwxzyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
RANDOM_STR_2 = "abcdefghijklmnopqrstuvwxzyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789~!@#$%^&*()_+=[]/?><,.`"

'''用户类型'''
UserType_Customer = 1
UserType_Shopper = 2

'''用户状态'''
UserStatus_Normal = 0
UserStatus_Pending_Review = 1
UserStatus_Dead = 2

ShopStatus_Normal = 0
ShopStatus_Reserve = 1
ShopStatus_Dead = 2

OrderStatus_Making = 0   #制作中
OrderStatus_ToFetch = 1   #待取餐
OrderStatus_Fetched = 2  #已取餐

# 软件密码，用于自己的接口间通信
R0_PASSWORD = "#eFaT&^uia92OP_+G+-]@!~4u56^%hs{adDHB"

'''一些辅助函数'''
# 生成长度为length的随机字符串，从choices中选取字符
def generate_random_codes(length,choices):
    r = ""
    for i in range(length):
        r += choices[random.randint(0,len(choices)-1)]
    return r

# 生成一个几乎不会重复的随机id
def generate_random_id():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S") + generate_random_codes(6,"0123456789")

# 检查登录状态和登录角色
def check_logined_and_role(role="anyRole"):
    if "logined" not in session or not session["logined"]:
        return False
    if "role" not in session:
        return False
    user_role = session.get("role",None)
    if role == "anyRole":
        return True
    return role == user_role