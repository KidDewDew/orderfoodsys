import random
from datetime import datetime

import shared
import db
import my_order
from flask import (make_response, session, render_template, request, jsonify)

#?WIDout_trade_no=1000&WIDsubject=%E7%83%A4%E8%98%91%E8%8F%87&WIDtotal_amount=112&WIDbody=%E6%AF%8F%E4%BD%8D%E7%9A%84

# 在这里添加url_rule到app
def add_url_rules(app):
    app.add_url_rule("/pay/alipay_return", view_func=alipay_return)
    app.add_url_rule("/pay/alipay_notify", view_func=alipay_notify)
    app.add_url_rule("/pay/simulate_pay_success", view_func=simulate_pay_success, methods=["POST"])


def create_alipay_order_url(subject,total_amount,describe):
    out_trade_no = shared.generate_random_id()
    # 由于Alipay给python的接口文档太少了，所以这里构建的付款url是指向tomcat 8080端口的
    url = (f"http://47.120.51.172:8080/alipay-wappay/wappay/pay.jsp?"
           f"WIDout_trade_no={out_trade_no}"
           f"&WIDsubject={subject}"
           f"&WIDtotal_amount={total_amount}"
           f"&WIDbody={describe}")
    return url,out_trade_no

def alipay_return():
    out_trade_no = request.args.get("out_trade_no",None)
    password = request.args.get("password")
    if password != shared.R0_PASSWORD: #验证R0密码是否正确
        return
    if out_trade_no is None:
        return
    # 支付宝回调：out_trade_no支付成功
    r = db.do_query("SELECT order_content,username,belong_shop,total_amount FROM alipay_trade"
                " WHERE out_trade_no=%s",(out_trade_no,))
    if len(r) == 0: return
    my_order.create_payed_making_order(r[0][0],r[0][1],r[0][2],r[0][3])

def alipay_notify():
    pass

#支付宝回调：支付失败
def alipay_failed():
    pass

# 模拟支付成功（用于测试）
def simulate_pay_success():
    """模拟支付成功，直接创建订单"""
    if not shared.check_logined_and_role("customer"):
        return jsonify({"errorMsg":"请登录"}),400
    
    out_trade_no = request.form.get("out_trade_no", None)
    if not out_trade_no:
        return jsonify({"errorMsg":"缺少订单号"}),400
    
    # 查询交易记录
    r = db.do_query("SELECT order_content,username,belong_shop,total_amount FROM alipay_trade WHERE out_trade_no=%s",(out_trade_no,))
    if not r or len(r) == 0:
        return jsonify({"errorMsg":"订单不存在"}),400
    
    # 创建订单
    order_id = my_order.create_payed_making_order(r[0][0], r[0][1], r[0][2], r[0][3])
    if order_id >= 0:
        return jsonify({"msg":"支付成功，订单已创建","order_id":order_id}),200
    else:
        return jsonify({"errorMsg":"创建订单失败"}),500

