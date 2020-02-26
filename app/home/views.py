# coding:utf8
from . import home
from flask import render_template, redirect, url_for, flash, session, request
from app.home.forms import RegistForm, LoginForm, UserdetailForm, PwdForm, CommentForm
from app.models import User, UserLog, Preview, Tag, Movie, Comment, Moviecol, Images
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps  # 登录装饰器
from app import db, app
import datetime
import uuid
import os


# 登录装饰器，限制管理员直接数据地址访问后台主页
def user_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("home.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


# 修改文件名称
def change_filename(filename):
    fileinfo = os.path.splitext(filename)
    filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex) + fileinfo[-1]
    return filename


# 视图
# 首页（标签筛选）
@home.route("/<int:page>/", methods=["GET", "POST"])
def index(page=None):
    tags = Tag.query.all()
    page_data = Movie.query
    # 标签
    tid = request.args.get("tid", 0)
    if int(tid) != 0:
        page_data = page_data.filter_by(tag_id=int(tid))
    # 星级
    star = request.args.get("star", 0)
    if int(star) != 0:
        page_data = page_data.filter_by(star=int(star))
    # 时间
    time = request.args.get("time", 0)
    if int(time) != 0:
        if int(time) == 1:
            page_data = page_data.order_by(
                Movie.addTime.desc()
            )
        else:
            page_data = page_data.order_by(
                Movie.addTime.asc()
            )
    # 播放量
    pm = request.args.get("pm", 0)
    if int(pm) != 0:
        if int(pm) == 1:
            page_data = page_data.order_by(
                Movie.playNum.desc()
            )
        else:
            page_data = page_data.order_by(
                Movie.playNum.asc()
            )
    # 评论量
    cm = request.args.get("cm", 0)
    if int(cm) != 0:
        if int(cm) == 1:
            page_data = page_data.order_by(
                Movie.commentNum.desc()
            )
        else:
            page_data = page_data.order_by(
                Movie.commentNum.asc()
            )
    # 分页
    if page is None:
        page = 1
    page_data = page_data.paginate(page=page, per_page=10)
    # 参数的字典
    p = dict(
        tid=tid,
        star=star,
        time=time,
        pm=pm,
        cm=cm,
    )
    return render_template("home/index.html", page_data=page_data, tags=tags, p=p)


# 用户登录
@home.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        user = User.query.filter_by(name=data["name"]).first()
        if user is None:
            flash("没有此用户", "err")
            return redirect(url_for("home.login"))
        if not user.check_pwd(data["pwd"]):
            flash("密码错误", "err")
            return redirect(url_for("home.login"))

        session["user"] = user.name
        session["user_id"] = user.id
        # 用户登录后，保存用户登录日志
        userLog = UserLog(
            user_id=user.id,
            ip=request.remote_addr,
        )
        db.session.add(userLog)
        db.session.commit()
        return redirect(url_for("home.user"))
    return render_template("home/login.html", form=form)


# 用户注销
@home.route("/logout/")
def logout():
    session.pop("user", None)
    session.pop("user_id", None)
    return redirect(url_for("home.login"))


# 用户注册界面
@home.route("/regist/", methods=["GET", "POST"])
def regist():
    form = RegistForm()
    if form.validate_on_submit():
        data = form.data
        user = User(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            pwd=generate_password_hash(data["pwd"]),
            uuid=uuid.uuid4().hex
        )
        print(user.name)
        db.session.add(user)
        db.session.commit()
        flash("注册成功", "ok")
    return render_template("home/regist.html", form=form)


# 会员修改资料
@home.route("/user/", methods=["POST", "GET"])
@user_login_req
def user():
    form = UserdetailForm()
    user = User.query.get(int(session["user_id"]))
    # form.face.validators = []
    if request.method == "GET":
        form.name.data = user.name
        form.email.data = user.email
        form.phone.data = user.phone
        form.info.data = user.info
    if form.validate_on_submit():
        data = form.data
        file_face = secure_filename(form.face.data.filename)
        # 如果路径不存在，就创建一个文件的目录，并授权读写
        if not os.path.exists(app.config["FC_DIR"]):
            os.makedirs(app.config["FC_DIR"])
            os.chmod(app.config["FC_DIR"], "rw")
        face = change_filename(file_face)
        form.face.data.save(app.config["FC_DIR"] + face)

        name_count = User.query.filter_by(name=data["name"]).count()
        if data["name"] != user.name and name_count == 1:
            flash("昵称已存在", "err")
            return redirect(url_for("home.user"))

        email_count = User.query.filter_by(email=data["email"]).count()
        if data["email"] != user.email and email_count == 1:
            flash("邮箱已存在", "err")
            return redirect(url_for("home.user"))

        phone_count = User.query.filter_by(phone=data["phone"]).count()
        if data["phone"] != user.phone and phone_count == 1:
            flash("手机号码已存在", "err")
            return redirect(url_for("home.user"))

        user.name = data["name"]
        user.email = data["email"]
        user.phone = data["phone"]
        user.info = data["info"]
        user.face = face
        db.session.add(user)
        db.session.commit()
        flash("修改成功", "ok")
        return redirect(url_for("home.user"))
    return render_template("home/user.html", form=form, user=user)


# 会员修改视图
@home.route("/pwd/", methods=["POST", "GET"])
@user_login_req
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        user = User.query.filter_by(name=session["user"]).first()
        if not user.check_pwd(data["old_pwd"]):
            flash("旧密码错误", "err")
            return redirect(url_for("home.pwd"))
        from werkzeug.security import generate_password_hash
        user.pwd = generate_password_hash(data["new_pwd"])
        db.session.add(user)
        db.session.commit()
        flash("修改密码成功，请重新登录", "ok")
        return redirect(url_for("home.logout"))
    return render_template("home/pwd.html", form=form)


# 评论记录
@home.route("/comments/<int:page>/")
@user_login_req
def comments(page=None):
    # 分页
    if page is None:
        page = 1
        # 关联查询
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Comment.movie_id,
        User.id == session["user_id"]
    ).order_by(
        Comment.addTime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("home/comments.html", page_data=page_data)


# 登录日志
@home.route("/loginlog/<int:page>/", methods=["GET", "POST"])
@user_login_req
def loginlog(page=None):
    if page is None:
        page = 1
        # 关联查询
    page_data = UserLog.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        UserLog.addTime.asc()
    ).paginate(page=page, per_page=10)
    return render_template("home/loginlog.html", page_data=page_data)


# 搜索功能
@home.route("/search/<int:page>/")
def search(page=None):
    if page is None:
        page = 1
    key = request.args.get("key", "")
    # 模糊查询
    movie_count = Movie.query.filter(
        Movie.title.ilike('%' + key + '%')
    ).count()
    page_data = Movie.query.filter(
        Movie.title.ilike('%' + key + '%')
    ).order_by(
        Movie.addTime.asc()
    ).paginate(page=page, per_page=10)
    print(movie_count)
    return render_template("home/search.html", movie_count=movie_count, key=key, page_date=page_data)


# 上映预告
@home.route("/animation/")
def animation():
    data = Preview.query.all()
    return render_template("home/animation.html", data=data)


# 电影详情,电影播放
@home.route("/play/<int:id>/<int:page>/", methods=["GET", "POST"])
def play(id=None, page=None):
    movie = Movie.query.join(Tag).filter(
        Tag.id == Movie.tag_id,
        Movie.id == int(id)
    ).first_or_404(int(id))
    # 分页
    if page is None:
        page = 1
        # 关联查询
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == movie.id,
        User.id == Comment.user_id
    ).order_by(
        Comment.addTime.desc()
    ).paginate(page=page, per_page=10)

    form = CommentForm()
    # 播放电影，电影的播放量加1
    movie.playNum = movie.playNum + 1
    if "user" in session and form.validate_on_submit():
        data = form.data
        comment = Comment(
            content=data["content"],
            movie_id=movie.id,
            user_id=session["user_id"]
        )
        # 提交评论
        db.session.add(comment)
        db.session.commit()
        # 电影的评论量+1
        movie.commentNum = movie.commentNum + 1
        db.session.add(movie)
        db.session.commit()
        # 评论提交成功，闪现一条消息
        flash("评论成功", "ok")
        return redirect(url_for("home.play", id=movie.id, page=1))
    db.session.add(movie)
    db.session.commit()
    return render_template("home/play.html", movie=movie, form=form, page_data=page_data)


# 添加电影收藏
@home.route("/moviecol/add/", methods=["GET"])
@user_login_req
def moviecol_add():
    uid = request.args.get("uid", "")
    mid = request.args.get("mid", "")
    moviecol = Moviecol.query.filter_by(
        user_id=int(uid),
        movie_id=int(mid)
    ).count()
    if moviecol == 1:
        data = dict(ok=0)
    if moviecol == 0:
        moviecol = Moviecol(
            user_id=int(uid),
            movie_id=int(mid)
        )
        db.session.add(moviecol)
        db.session.commit()
        data = dict(ok=1)
    import json
    # 异步提交
    return json.dumps(data)


# 电影收藏
@home.route("/moviecol/<int:page>/")
@user_login_req
def moviecol(page=None):
    if page is None:
        page = 1
        # 关联查询
    page_data = Moviecol.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Moviecol.movie_id,
        User.id == session["user_id"]
    ).order_by(
        Moviecol.addTime.asc()
    ).paginate(page=page, per_page=10)
    return render_template("home/moviecol.html", page_data=page_data)


# 图片
@home.route("/images/<int:page>/")
@user_login_req
def images(page=None):
    if page is None:
        page = 1
    page_data = Images.query.order_by(
        Images.id.asc()
    ).paginate(page=page, per_page=1)

    print(page_data.items)
    return render_template("home/images.html", page_data=page_data)


