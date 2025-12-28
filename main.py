import os

import auth
import db
import shared
from flask import (Flask, request, render_template, make_response,
                   redirect, url_for, jsonify, session)
import api
import shop
import pay
import my_order

app = Flask(__name__)


@app.route("/")
def index():
    if not shared.check_logined_and_role():
        session["login_then"] = "index" #登录完成后，回到index
        return redirect(url_for('static_proxy',path='login'))
    return redirect(url_for('shoplist_page'))

@app.route("/<path:path>",methods=['GET'])
def static_proxy(path):
    if path != "login" and not shared.check_logined_and_role():
        return redirect(url_for('static_proxy',path='login'))
    return app.send_static_file(path+'.html')


''' main 入口 '''
if __name__ == "__main__":
    print("工作路径 is", os.getcwd())

    # 添加其他文件定义的url_rule.
    api.add_url_rules(app)
    shop.add_url_rules(app)
    pay.add_url_rules(app)
    auth.add_url_rules(app)
    my_order.add_url_rules(app)

    app.secret_key = shared.generate_random_codes(16,shared.RANDOM_STR_2)
    app.run(host="0.0.0.0")

    # 关闭与数据库的所有连接