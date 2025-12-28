import hashlib

import shared
import db
from flask import (make_response, session, request, jsonify)
from captcha.image import ImageCaptcha  #验证码生成

from shared import UserStatus_Pending_Review, UserStatus_Normal


# 在这里添加url_rule到app
def add_url_rules(app):
    app.add_url_rule("/api/login", view_func=api_login, methods=["POST"])
    app.add_url_rule("/api/exit_login", view_func=api_exit_login)
    app.add_url_rule("/api/register", view_func=api_register, methods=["POST"])
    app.add_url_rule("/api/pass_shopper", view_func=pass_shopper, methods=["POST"])

def api_login():
    username = request.form.get('username')
    password = request.form.get('password')
    verify_code = request.form.get('verify_code')
    
    # 验证验证码（先验证验证码，避免不必要的数据库查询）
    session_verify_code = session.pop('verify_code', None)
    if not verify_code or verify_code != session_verify_code:
        return jsonify({"errorMsg":"验证码错误"}),400

    # 验证用户名和密码
    r = db.do_query("SELECT password_md5,user_type,user_status FROM user WHERE username=%s",(username,))

    if not r or len(r) == 0:
        return jsonify({"errorMsg":"该用户不存在"}),400
    
    if r[0][2] == shared.UserStatus_Dead:
        return jsonify({"errorMsg":"该用户已被禁用"}),400

    if hashlib.md5(password.encode()).hexdigest().lower() != r[0][0].lower():
        return jsonify({"errorMsg":"密码错误"}),400

    if r[0][2] == shared.UserStatus_Pending_Review:
        return jsonify({"errorMsg": "该商户用户正在审核中...详细情况可以联系刘硕(18118033672)"}), 400

    # 记录登录的状态
    session["logined"] = True
    session["username"] = username
    session["role"] = "customer" if r[0][1] == shared.UserType_Customer else "shopper"

    if r[0][1] == shared.UserType_Customer:
        goto_url = "/shoplist"
    else:
        #对于shopper用户，需要查询该用户的店铺id
        r = db.do_query("SELECT shop_id FROM user_shop WHERE username=%s",(username,))
        if not r or len(r) == 0:
            return jsonify({"errorMsg": "账号异常，请联系.."}), 400
        shop_id = r[0][0]
        goto_url = f"/shop/{shop_id}"

    return jsonify({"redirect":goto_url}),200

def api_exit_login():
    pass

# 审核通过商家账号，同时创建商家账户下的shop
# 该接口默认只由管理员调用
def pass_shopper():
    password = request.form.get("password")
    print("pwd:",password)
    if password != shared.R0_PASSWORD:
        return "密码错误",400
    shop_user = request.form.get("shop_user")
    try:
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_status FROM user WHERE username=%s",(shop_user,))
        r = cursor.fetchall()
        if len(r) == 0:
            return "商家用户不存在",400
        if r[0][0] != shared.UserStatus_Pending_Review:
            return "商家用户不处于待审核状态",400

        cursor.execute(f"UPDATE user SET user_status={shared.UserStatus_Normal} WHERE username=%s",(shop_user,))

        # 创建shop，创建关联
        cursor.execute(f"INSERT INTO shop (shop_position,status,shop_name) VALUES "
                       f"(\"暂无定位\",{shared.ShopStatus_Reserve},\"未设置\")")
        cursor.execute("INSERT INTO user_shop (username,shop_id) VALUES (%s,(SELECT LAST_INSERT_ID()))",(shop_user,))
        conn.commit()
        return "success",200
    except Exception as e:
        print(e)
        conn.rollback()
        return "数据库写入失败", 400
    finally:
        cursor.close()

def api_register():
    print(request.form)
    username = request.form.get('username')
    password = request.form.get('password')
    userType = request.form.get('userType')
    verify_code = request.form.get('verify_code')
    if verify_code != session.pop('verify_code', None):
        return jsonify({"errorMsg": "验证码错误"}), 400

    # 查询是否有重复的用户名(上锁)
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM user WHERE username = %s",(username,))
    if len(cursor.fetchall()) > 0:
        cursor.close()
        return jsonify({"errorMsg":"该用户名已经被别人注册过了"}),400

    password_md5 = hashlib.md5(password.encode()).hexdigest()
    userType = shared.UserType_Customer if userType == "customer" else shared.UserType_Shopper
    status = shared.UserStatus_Normal if userType == shared.UserType_Customer else shared.UserStatus_Pending_Review
    try:
        cursor.execute("INSERT INTO user (username,password_md5,user_type,user_status) VALUES (%s,%s,%s,%s)",
                       (username,password_md5,userType,status))
    except Exception as e:
        print(e)
        cursor.close()
        conn.rollback()
        return "{}",400
    cursor.close()
    conn.commit()
    if userType == shared.UserType_Customer:
        return "{\"msg\":\"注册成功，请登录\"}"
    else: return "{\"msg\":\"注册成功，请联系刘硕18118033672，激活商家账号\"}"


