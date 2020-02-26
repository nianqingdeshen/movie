# coding:utf8
import os

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import config

app = Flask(__name__)
# app.config.from_object(config)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@localhost:3306/db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["SECRET_KEY"] = "2daad74e25c0437181507d9be1c51354"
# 电影和电影封面保存路径
app.config["UP_DIR"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/uploads/")
# 用户头像保存路径
app.config["FC_DIR"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/uploads/user/")
app.debug = True
db = SQLAlchemy(app)

from app.admin import admin as admin_blueprint
from app.home import home as home_blueprint

app.register_blueprint(home_blueprint)
app.register_blueprint(admin_blueprint, url_prefix="/admin")


# 错误页面
@app.errorhandler(404)
def page_not_found(error):
    return render_template("home/404.html"), 404
