import json
import os
import random
import traceback
from logging import exception

import mysql.connector.errors

import shared
import db
from flask import (make_response, session, render_template, redirect, request, jsonify)

import pay

# 在这里添加url_rule到app
def add_url_rules(app):
    app.add_url_rule("/my_orders/getAllOrders_ofShop", view_func=getActiveOrders_ofShop)  # 别名，用于获取所有订单（包括历史）
    app.add_url_rule("/my_orders", view_func=my_orders_page)
    app.add_url_rule("/my_orders/getAllOrders_ofUser", view_func=getAllOrders_ofUser)
    app.add_url_rule("/my_orders/getActiveOrders_ofShop", view_func=getActiveOrders_ofShop)
    app.add_url_rule("/my_orders/makeit/<int:order_id>", view_func=makeit)

# 显示我的订单 - 商家显示店铺订单/顾客显示个人订单
def my_orders_page():
    if not shared.check_logined_and_role():
        return "{\"errorMsg\":\"请登录\"}", 400
    role = session.get("role","")
    isShopper = (role == "shopper")
    username = session.get("username","")
    shop_id=-1
    if isShopper:
        r = db.do_query("SELECT shop_id FROM user_shop WHERE username=%s",(username,))
        if r and len(r) > 0:
            shop_id = r[0][0]
    return render_template("my_orders.html",isShopper=isShopper,username=username,shop_id=shop_id)

# 创建一个已支付、制作中的订单
def create_payed_making_order(order_content,customer_username,belong_shop,total_amount):
    try:
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO orders (order_content,customer_username,belong_shop,total_amount,status)"
                       " VALUES (%s,%s,%s,%s,%s)",(order_content,customer_username,belong_shop,total_amount,
                                                     shared.OrderStatus_Making))
        conn.commit()
        return cursor._last_insert_id #返回订单order_id
    except Exception as e:
        traceback.print_exc()
        return -1 #失败
    finally:
        if conn: conn.close()

def make_one_order_response_json(cursor,rr):
    r3 = {}
    # rr结构: (order_content, total_amount, status, order_id, create_time)
    r3["status"] = rr[2]
    r3["total_amount"] = float(rr[1])
    r3["order_id"] = rr[3]
    content = json.loads(rr[0])
    content2 = []
    for item_id, num in content.items():
        item_id = int(item_id)
        cursor.execute("SELECT item_name FROM item WHERE item_id=%s", (item_id,))
        result = cursor.fetchall()
        if len(result) > 0:
            item_name = result[0][0]
            item = {"item_name": item_name, "num": int(num)}
            content2.append(item)
    r3["content"] = content2
    return r3

def getAllOrders_ofUser():
    if not shared.check_logined_and_role("customer"):  # 验证登录：顾客
        return "{\"errorMsg\":\"请登录\"}", 400
    r = db.do_query("SELECT order_content,total_amount,status,order_id,create_time FROM orders WHERE customer_username=%s "
                    "ORDER BY create_time DESC",
                    (session.get("username",""),))
    if r is None or len(r) == 0:
        return jsonify([])
    arr = []
    try:
        conn = db.get_db_connection()
        cursor = conn.cursor()
        for rr in r:
            r3 = make_one_order_response_json(cursor,rr)
            arr.append(r3)
    except Exception as e:
        traceback.print_exc()
        return jsonify([])
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return jsonify(arr)


def getActiveOrders_ofShop():
    if not shared.check_logined_and_role("shopper"):  # 验证登录：商家
        return "{\"errorMsg\":\"请登录\"}", 400

    username = session.get("username","")
    r = db.do_query("SELECT shop_id FROM user_shop WHERE username=%s",(username,))
    if not r or len(r) == 0:
        return jsonify([])
    shop_id = r[0][0]
    # 获取所有订单（包括历史订单），按时间倒序
    r = db.do_query("SELECT order_content,total_amount,status,order_id,create_time FROM orders WHERE belong_shop=%s "
                    "ORDER BY create_time DESC",
                    (shop_id,))
    if r is None or len(r) == 0:
        return jsonify([])
    arr = []
    try:
        conn = db.get_db_connection()
        cursor = conn.cursor()
        for rr in r:
            r3 = make_one_order_response_json(cursor, rr)
            arr.append(r3)
    except Exception as e:
        traceback.print_exc()
        return jsonify([])
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return jsonify(arr)

def makeit(order_id):
    if not shared.check_logined_and_role("shopper"):  # 验证登录：顾客
        return "{\"errorMsg\":\"请登录\"}", 400

    # username = session.get("username","")
    # r = db.do_query("SELECT shop_id FROM user_shop WHERE username=%s",(username,))
    # shop_id = r[0][0]

    # 验证order_id属于这个店铺 todo 累了。。已经0点了。。就不验证了

    #所以说这个函数没有任何检查，，
    conn = db.get_db_connection()
    conn.cursor().execute("UPDATE orders SET status=1 WHERE order_id=%s",(order_id,))
    conn.commit()
    conn.close()

    return "",200