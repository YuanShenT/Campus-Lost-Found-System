# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from config import Config  # 从 config.py 导入配置
from models import db, User, Item, Message # 确保 Item 模型已导入
from flask_migrate import Migrate

from datetime import datetime # 用于处理日期时间
import os # 用于文件路径操作
from werkzeug.utils import secure_filename # 用于安全处理上传的文件名
from datetime import datetime, timezone, timedelta
from sqlalchemy import or_ , and_ # 用于查询消息列表时合并发送和接收
import jieba # 导入 jieba 分词库

from flask_mail import Mail, Message as FlaskMessage # 将 Flask-Mail 的 Message 类重命名为 FlaskMessage 避免与我们自己的 Message 模型冲突

app = Flask(__name__)
app.config.from_object(Config) # 加载配置

db.init_app(app) # 初始化 SQLAlchemy
migrate = Migrate(app, db) # 在 db.init_app(app) 之后添加


# 初始化 Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # 设置未登录用户重定向的登录视图函数名
login_manager.login_message_category = 'info' # 未登录提示消息的类别

# --- 邮件配置 ---
# 这里你需要替换成你的SMTP服务器信息
# 推荐使用像 Gmail, QQ邮箱, 163邮箱等常见的SMTP服务
# 以Gmail为例，你可能需要开启“两步验证”并生成“应用专用密码”，而不是直接使用你的邮箱密码
app.config['MAIL_SERVER'] = 'smtp.qq.com'  # 例如：'smtp.gmail.com' (Gmail), 'smtp.163.com' (163邮箱)
app.config['MAIL_PORT'] = 465             # Gmail/QQ邮箱通常使用 465 或 587
app.config['MAIL_USE_SSL'] = True         # 对于 465 端口通常是 True，对于 587 端口通常是 MAIL_USE_TLS = True
app.config['MAIL_USE_TLS'] = False        # 根据你的邮件服务商选择，如果 MAIL_USE_SSL 是 True，这个通常是 False
app.config['MAIL_USERNAME'] = '1696280515@qq.com' # 你的邮箱地址
app.config['MAIL_PASSWORD'] = 'zmsapoekzemweaij'  # QQ邮箱是授权码，Gmail是应用专用密码，不是你的登录密码
app.config['MAIL_DEFAULT_SENDER'] = '1696280515@qq.com' # 默认发件人

mail = Mail(app)


MAP_REGIONS = {
    '运动场': {'min_x': 0, 'min_y': 0, 'max_x': 466, 'max_y': 488},
    '雁北': {'min_x': 466, 'min_y': 0, 'max_x': 714, 'max_y': 488},
    '食堂': {'min_x': 714, 'min_y': 0, 'max_x': 910, 'max_y': 488},
    '综合办公楼': {'min_x': 910, 'min_y': 0, 'max_x': 1134, 'max_y': 239},
    '学生活动中心': {'min_x': 910, 'min_y': 239, 'max_x': 1134, 'max_y': 488},
    '图书馆': {'min_x': 1134, 'min_y': 0, 'max_x': 1524, 'max_y': 488},
    '网安楼': {'min_x': 1524, 'min_y': 0, 'max_x': 1891, 'max_y': 488},
    '雁南': {'min_x': 44, 'min_y': 535, 'max_x': 709, 'max_y': 1136},
    '教学楼': {'min_x': 727, 'min_y': 533, 'max_x': 1106, 'max_y': 802},
    '学生食堂': {'min_x': 721, 'min_y': 962, 'max_x': 959, 'max_y': 1130},
    's1楼': {'min_x': 1533, 'min_y': 536, 'max_x': 1845, 'max_y': 945},
    '理学院': {'min_x': 1528, 'min_y': 960, 'max_x': 1891, 'max_y': 1136},

    # 更多区域可以继续添加...
    # 例如，如果地图尺寸是 700x500，这些坐标应在 0 到 700 和 0 到 500 之间
}



def send_async_email(app, msg):
    """异步发送邮件的辅助函数"""
    with app.app_context():
        try:
            mail.send(msg)
            app.logger.info(f"邮件已发送到: {msg.recipients}")
        except Exception as e:
            app.logger.error(f"邮件发送失败到 {msg.recipients}: {e}", exc_info=True)


def send_email_notification(to_email, subject, template_name, **kwargs):
    """
    发送邮件通知的通用函数。
    to_email: 收件人邮箱
    subject: 邮件主题
    template_name: 邮件内容模板文件名 (例如 'email_new_message.html')
    kwargs: 传递给模板的变量
    """
    msg = FlaskMessage(subject, recipients=[to_email])
    # 渲染邮件内容，你可以为邮件内容创建独立的HTML模板
    msg.html = render_template(f'emails/{template_name}', **kwargs)

    # 在实际应用中，通常会使用线程或任务队列（如 Celery）来异步发送邮件，
    # 以避免阻塞主应用进程。这里我们先简单地使用一个新线程来模拟异步发送。
    # 对于简单的应用，直接调用 mail.send(msg) 也可以，但用户可能需要等待几秒。
    from threading import Thread
    Thread(target=send_async_email, args=(app, msg)).start()


# 在应用上下文内创建所有数据库表
# 第一次运行此应用时执行，或者当你的模型有修改时执行。
# 确保你的 MySQL 数据库 `lost_and_found` 已经存在。

with app.app_context():
    db.create_all() # <--- db 和模型现在已经完全初始化


def find_matching_items(new_item):
    """
    根据新发布的物品信息，查找潜在的匹配物品。
    此版本修正了之前对 Python 字符串调用 .like() 的错误。
    继续使用 SQLAlchemy 的 .like() 进行模糊匹配。

    :param new_item: 刚刚发布的 Item 对象
    :return: 匹配的 Item 对象列表
    """
    matches = []
    # 确定要搜索的物品类型（如果新发布的是失物，则搜索拾物；反之亦然）
    target_type = 'found' if new_item.type == 'lost' else 'lost'

    # 定义匹配关键词：使用 Jieba 对物品名称和描述进行分词
    text_to_segment = new_item.name
    if new_item.description:  # 只有当 description 不为 None 时才拼接
        text_to_segment += " " + new_item.description

    # 使用 Jieba 精确模式分词
    raw_keywords = jieba.cut_for_search(text_to_segment)

    # 过滤掉通用词汇和单字词
    stop_words = set([
        '是', '的', '了', '在', '我', '你', '他', '她', '它', '和', '或者',
        '一个', '一部', '一些', '发生', '发现', '丢失', '捡到', '地方', '物品', '东西',
        '什么', '谁', '于', '上', '下', '里', '外', '将', '把', '被', '对', '等等'
    ])

    filtered_search_terms = []
    for term in raw_keywords:
        term = term.strip().lower()
        if len(term) > 1 and term not in stop_words:
            filtered_search_terms.append(term)

    # 去重
    search_terms = list(set(filtered_search_terms))
    app.logger.info(f"Jieba分词后关键词: {search_terms}")

    # 构建关键词搜索条件
    keyword_conditions = []
    if search_terms:
        for term in search_terms:
            # 确保对 Item.name 和 Item.description 使用 like()
            keyword_conditions.append(Item.name.like(f'%{term}%'))
            # 只有当 Item.description 字段可能包含该关键词时才添加条件
            keyword_conditions.append(Item.description.like(f'%{term}%'))

    # 构建地点搜索条件
    location_conditions = []
    # 原始地点精确匹配（保持这个，它仍然有用）
    location_conditions.append(Item.location == new_item.location)

    # 对 new_item.location 进行分词，并构建模糊匹配条件
    if new_item.location:  # 确保 new_item.location 不为 None
        raw_location_keywords = jieba.cut_for_search(new_item.location)
        location_search_terms = [
            loc_term.strip().lower() for loc_term in raw_location_keywords if len(loc_term.strip()) > 0
        ]
        app.logger.info(f"Jieba分词后地点关键词: {location_search_terms}")

        # 增加基于地点分词的模糊匹配
        for loc_term in location_search_terms:
            location_conditions.append(Item.location.like(f'%{loc_term}%'))

    # 此外，仍然可以考虑新地点包含旧地点，或旧地点包含新地点
    # 这条是正确的，Item.location 是 ORM 列
    location_conditions.append(Item.location.like(f'%{new_item.location}%'))
    # ！！！！！ 已删除引起错误的行：new_item.location.like(f'%{Item.location}%') ！！！！！

    # 构建时间范围条件
    time_delta_days = 7
    # 确保 new_item.event_time 是 datetime 对象
    time_start = new_item.event_time - timedelta(days=time_delta_days)
    time_end = new_item.event_time + timedelta(days=time_delta_days)
    time_condition = Item.event_time.between(time_start, time_end)

    # # 组合所有条件
    base_conditions = [
        Item.type == target_type,
        Item.status == 'active',
        Item.user_id != new_item.user_id  # 不匹配自己发布的物品
    ]

    # 构建最终的组合条件
    combined_main_condition_parts = []
    if keyword_conditions:
        combined_main_condition_parts.append(or_(*keyword_conditions))
    if location_conditions:
        combined_main_condition_parts.append(or_(*location_conditions))

    if not combined_main_condition_parts:  # 如果没有任何有效的关键词或地点条件，则不进行匹配
        return []

    # 将关键词和地点条件组合起来
    final_complex_condition = or_(*combined_main_condition_parts)

    # 执行查询
    try:
        matches = Item.query.filter(
            *base_conditions,
            final_complex_condition,
            time_condition  # 时间条件必须满足
        ).all()
    except Exception as e:
        # 记录更详细的错误信息，帮助诊断
        app.logger.error(f"匹配查询失败，可能参数或SQL语句问题: {e}", exc_info=True)
        matches = []

    return matches

@login_manager.user_loader
def load_user(user_id):
    """
    这个回调函数用于从用户 ID 加载用户对象。
    Flask-Login 会在需要时（例如从会话中）调用它。
    """
    return User.query.get(int(user_id))




@app.route('/')
@app.route('/')
def index():
    """
    主页视图，显示用户的登录状态和最新的物品信息，并支持搜索和区域筛选功能。
    """
    # 获取搜索参数
    search_query = request.args.get('query', '').strip() # 关键词
    item_type_filter = request.args.get('type', '').strip() # 物品类型 (lost/found)
    region_name = request.args.get('region_name', '').strip() # 获取区域名称，默认为空字符串

    # 构建基础查询
    # --- 修正为 posted_date 进行排序 ---
    items_query = Item.query.order_by(Item.posted_date.desc())

    # 根据搜索关键词筛选
    if search_query:
        items_query = items_query.filter(
            or_(
                Item.name.ilike(f'%{search_query}%'),
                Item.description.ilike(f'%{search_query}%'),
                Item.location.ilike(f'%{search_query}%')
            )
        )

    # 根据物品类型筛选
    if item_type_filter and item_type_filter in ['lost', 'found']:
        items_query = items_query.filter_by(type=item_type_filter)

    # 根据区域筛选物品
    # 只有当 region_name 不为空且在 MAP_REGIONS 中存在时才进行筛选
    if region_name and region_name in MAP_REGIONS:
        region_coords = MAP_REGIONS[region_name]
        min_x = region_coords['min_x']
        min_y = region_coords['min_y']
        max_x = region_coords['max_x']
        max_y = region_coords['max_y']

        items_query = items_query.filter(
            Item.pin_x.isnot(None), # 确保 pin_x 不为空
            Item.pin_y.isnot(None), # 确保 pin_y 不为空
            Item.pin_x >= min_x,
            Item.pin_x <= max_x,
            Item.pin_y >= min_y,
            Item.pin_y <= max_y
        )

    # 执行查询
    items = items_query.all()

    # 将查询到的物品列表、搜索参数和地图区域数据传递给模板
    return render_template('index.html',
                           user=current_user,
                           items=items,
                           search_query=search_query,
                           item_type_filter=item_type_filter,
                           MAP_REGIONS=MAP_REGIONS, # <--- 传递 MAP_REGIONS
                           selected_region=region_name) # <--- 传递当前选中的区域
# def index():
#     """
#     主页视图，显示用户的登录状态和最新的物品信息，并支持搜索功能。
#     """
#     # 获取搜索参数
#     search_query = request.args.get('query', '').strip() # 关键词
#     item_type_filter = request.args.get('type', '').strip() # 物品类型 (lost/found)
#
#     # 构建基础查询
#     items_query = Item.query.order_by(Item.posted_date.desc())
#
#     # 根据搜索关键词筛选
#     if search_query:
#         # 使用 ilike 进行不区分大小写的模糊匹配
#         # 搜索物品名称或描述中包含关键词的物品
#         items_query = items_query.filter(
#             (Item.name.ilike(f'%{search_query}%')) |
#             (Item.description.ilike(f'%{search_query}%')) |
#             (Item.location.ilike(f'%{search_query}%')) # 也可以搜索地点
#         )
#
#     # 根据物品类型筛选
#     if item_type_filter and item_type_filter in ['lost', 'found']:
#         items_query = items_query.filter_by(type=item_type_filter)
#
#     # 执行查询
#     items = items_query.all()
#
#     # 将查询到的物品列表和搜索参数传递给模板
#     return render_template('index.html',
#                            user=current_user,
#                            items=items,
#                            search_query=search_query, # 传递回模板，用于保留搜索框内容
#                            item_type_filter=item_type_filter) # 传递回模板，用于保留类型选择



@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    用户注册视图。
    处理 GET 请求时显示注册表单，处理 POST 请求时进行注册逻辑。
    """
    # 如果用户已经登录，则重定向到主页，避免重复注册。
    if current_user.is_authenticated:
        flash('您已登录，无需重复注册。', 'info')
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # 服务器端表单验证
        if not all([username, email, password, confirm_password]):
            flash('所有字段都不能为空！', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('两次输入的密码不一致！', 'danger')
            return redirect(url_for('register'))

        # 检查用户名和邮箱是否已被占用
        if User.query.filter_by(username=username).first():
            flash('用户名已被占用！', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册！', 'danger')
            return redirect(url_for('register'))

        # 创建新用户并保存到数据库
        new_user = User(username=username, email=email)
        new_user.set_password(password) # 对密码进行哈希处理

        try:
            db.session.add(new_user)
            db.session.commit() # 提交事务到数据库
            flash('注册成功！请登录。', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback() # 如果发生错误，回滚事务
            flash(f'注册失败，请稍后再试。错误信息: {e}', 'danger')
            # 生产环境中，此处应记录更详细的错误日志
            return redirect(url_for('register'))

    return render_template('register.html') # GET 请求时渲染注册表单

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    用户登录视图。
    处理 GET 请求时显示登录表单，处理 POST 请求时进行登录逻辑。
    """
    # 如果用户已经登录，则重定向到主页。
    if current_user.is_authenticated:
        flash('您已登录。', 'info')
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # 获取“记住我”选项，如果被勾选，其值为 'on'
        remember = request.form.get('remember_me') == 'on'

        user = User.query.filter_by(username=username).first()

        # 验证用户名和密码
        if user and user.check_password(password):
            login_user(user, remember=remember) # 使用 Flask-Login 登录用户
            flash('登录成功！', 'success')
            # 登录成功后，如果用户是尝试访问受保护页面而被重定向到登录页的，
            # 那么请求参数中会有 `next` URL，我们应该重定向回那个页面。
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index')) # 如果没有 next 页面，则重定向到主页
        else:
            flash('用户名或密码不正确。', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html') # GET 请求时渲染登录表单

@app.route('/logout')
@login_required # 只有已登录的用户才能访问此路由
def logout():
    """
    用户登出视图。
    """
    logout_user() # 使用 Flask-Login 登出用户
    flash('您已成功退出登录。', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required # 只有登录用户才能访问个人中心
def dashboard():
    """
    个人中心视图，显示当前用户发布的所有物品。
    """
    # 查询当前用户发布的所有物品，按发布时间降序排列
    # current_user 是 Flask-Login 提供的当前登录用户对象
    user_items = Item.query.filter_by(user_id=current_user.id).order_by(Item.posted_date.desc()).all()

    # 将物品列表传递给模板
    return render_template('user_dashboard.html', user_items=user_items)


#上传丢失或拾取的物品图片
UPLOAD_FOLDER = 'static/uploads' # 图片将保存到这个文件夹
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} # 允许的图片文件类型

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# 在 Flask 应用启动时确保上传文件夹存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 辅助函数：检查文件类型是否允许
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/publish', methods=['GET', 'POST'])
@login_required # 只有登录用户才能发布信息
def publish_item():
    """
    处理物品发布（失物或拾物）的视图函数。
    GET 请求显示发布表单，POST 请求处理表单提交。
    """
    if request.method == 'POST':
        item_type = request.form.get('item_type')
        name = request.form.get('name')
        description = request.form.get('description')
        location = request.form.get('location')
        event_time_str = request.form.get('event_time') # 从前端获取的是字符串
        pin_x_str = request.form.get('pin_x')
        pin_y_str = request.form.get('pin_y')

        # 将字符串坐标转换为整数，如果为空则为 None
        # 图钉坐标是可选的，所以允许为 None
        pin_x = int(pin_x_str) if pin_x_str else None
        pin_y = int(pin_y_str) if pin_y_str else None
        # --- 数据校验 ---
        if not all([item_type, name, location, event_time_str]):
            flash('请填写所有必填字段！', 'danger')
            return redirect(url_for('publish_item'))

        if item_type not in ['lost', 'found']:
            flash('信息类型无效！', 'danger')
            return redirect(url_for('publish_item'))

        try:
            # 将前端传来的 datetime-local 字符串转换为 datetime 对象
            # 格式示例: "2025-06-30T14:30"
            event_time = datetime.strptime(event_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('发生时间格式不正确！', 'danger')
            return redirect(url_for('publish_item'))

        image_filename = 'default.jpg' # 默认图片名
        # --- 图片上传处理 ---
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                # 确保文件名安全，防止路径遍历攻击
                filename = secure_filename(file.filename)
                # 构建图片保存路径
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                try:
                    file.save(image_path)
                    image_filename = filename # 保存到数据库的文件名
                except Exception as e:
                    flash(f'图片上传失败：{e}', 'danger')
                    # 可以选择继续发布不带图片的物品，或者直接返回
                    # 这里我们选择继续，但不会保存图片文件名
                    image_filename = 'default.jpg'
                    app.logger.error(f"图片上传失败: {e}") # 记录错误以便调试
            elif file.filename != '': # 用户选择了文件但文件类型不允许
                 flash('不支持的文件类型！请上传图片（png, jpg, jpeg, gif）。', 'danger')
                 return redirect(url_for('publish_item'))

        # --- 创建 Item 对象并保存到数据库 ---
        try:
            new_item = Item(
                type=item_type,
                name=name,
                description=description,
                location=location,
                event_time=event_time,
                image_file=image_filename,
                user_id=current_user.id, # 发布者是当前登录用户
                posted_date=datetime.utcnow(), # 记录发布到数据库的当前 UTC 时间
                pin_x=pin_x, # 保存图钉X坐标
                pin_y=pin_y  # 保存图钉Y坐标
            )
            db.session.add(new_item)
            db.session.commit()
            flash('信息发布成功！', 'success')
            # --- 触发智能匹配 ---
            matching_items = find_matching_items(new_item)
            if matching_items:
                app.logger.info(f"为新物品 '{new_item.name}' 找到了 {len(matching_items)} 个匹配项。")
                # 遍历所有匹配项，向相关用户发送邮件通知
                for match in matching_items:
                    # 向新物品的发布者发送通知（有匹配的旧物品）
                    if new_item.user.email:
                        send_email_notification(
                            to_email=new_item.user.email,
                            subject=f'校园失物招领：您的物品 "{new_item.name}" 可能有匹配！',
                            template_name='email_match_notification.html',  # 我们稍后会创建这个模板
                            current_item=new_item,
                            matching_item=match,
                            recipient_username=new_item.user.username
                        )
                    # 向匹配物品的发布者发送通知（有匹配的新物品）
                    if match.author.email:
                        send_email_notification(
                            to_email=match.author.email,
                            subject=f'校园失物招领：您的物品 "{match.name}" 可能有匹配！',
                            template_name='email_match_notification.html',  # 同样使用这个模板
                            current_item=match,
                            matching_item=new_item,
                            recipient_username=match.author.username
                        )
            else:
                app.logger.info(f"为新物品 '{new_item.name}' 未找到匹配项。")

            return redirect(url_for('item_detail', item_id=new_item.id))
        except Exception as e:
            db.session.rollback()
            flash(f'信息发布失败，请稍后再试。错误信息: {e}', 'danger')
            app.logger.error(f"信息发布失败: {e}") # 记录错误以便调试
            return redirect(url_for('publish_item'))

    # GET 请求时渲染发布表单
    return render_template('publish_item.html')


@app.route('/item/<int:item_id>')
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    # 传递原始地图尺寸给模板，以便前端进行比例转换
    # 确保这里的尺寸和你 map.png 的原始像素尺寸一致
    ORIGINAL_MAP_WIDTH = 1887
    ORIGINAL_MAP_HEIGHT = 1183

    return render_template('item_detail.html',
                           item=item,
                           ORIGINAL_MAP_WIDTH=ORIGINAL_MAP_WIDTH,
                           ORIGINAL_MAP_HEIGHT=ORIGINAL_MAP_HEIGHT)

# --- 物品编辑功能 ---
# app.py

# ... (确保你导入了 Item 和 User 模型) ...

@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
@login_required  # 确保只有登录用户才能编辑
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    # 确保只有物品的发布者才能编辑
    if item.user != current_user:
        flash('您无权编辑此信息。', 'danger')
        return redirect(url_for('dashboard'))

    # 确保这里的尺寸和你 map.png 的原始像素尺寸一致
    ORIGINAL_MAP_WIDTH = 1887
    ORIGINAL_MAP_HEIGHT = 1183

    if request.method == 'POST':
        item.name = request.form['name']
        item.description = request.form['description']
        item.location = request.form['location']
        item.event_time = datetime.strptime(request.form['event_time'], '%Y-%m-%dT%H:%M')

        # 处理图片上传
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                # 删除旧图片（如果不是默认图片）
                if item.image_file and item.image_file != 'default.jpg':
                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_file)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)

                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                item.image_file = filename
            elif file.filename == '':  # 用户没有选择新文件但提交了表单
                pass  # 保持原图片
            # else: # 文件不被允许，可以给用户一个flash消息
            #    flash('图片文件类型不被允许。', 'warning')

        # 获取地图坐标
        # 注意：这里接收的 pin_x 和 pin_y 已经是转换到原始图片尺寸的坐标了
        pin_x = request.form.get('pin_x')
        pin_y = request.form.get('pin_y')

        # 转换为整数或None
        item.pin_x = int(pin_x) if pin_x and pin_x.isdigit() else None
        item.pin_y = int(pin_y) if pin_y and pin_y.isdigit() else None

        try:
            db.session.commit()
            flash('信息更新成功！', 'success')
            return redirect(url_for('item_detail', item_id=item.id))
        except Exception as e:
            db.session.rollback()
            flash(f'更新信息失败: {e}', 'danger')

    # GET 请求时渲染表单，并传递当前物品信息
    # 格式化 event_time 以便 datetime-local input 预填充
    formatted_event_time = item.event_time.strftime('%Y-%m-%dT%H:%M') if item.event_time else ''

    return render_template('edit_item.html',
                           item=item,
                           formatted_event_time=formatted_event_time,
                           ORIGINAL_MAP_WIDTH=ORIGINAL_MAP_WIDTH,
                           ORIGINAL_MAP_HEIGHT=ORIGINAL_MAP_HEIGHT)


# --- 物品删除功能 ---
@app.route('/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    """
    删除物品信息。只接受 POST 请求以避免 CSRF 风险。
    """
    item = Item.query.get_or_404(item_id)

    # 确保只有物品的发布者才能删除
    if item.author != current_user:
        flash('您无权删除此物品。', 'danger')
        return redirect(url_for('dashboard'))

    try:
        # 删除关联的图片文件（如果不是默认图片）
        if item.image_file and item.image_file != 'default.jpg':
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_file)
            if os.path.exists(image_path):
                os.remove(image_path)

        db.session.delete(item)
        db.session.commit()
        flash('物品已成功删除！', 'success')
        return redirect(url_for('dashboard'))  # 删除后返回个人中心
    except Exception as e:
        db.session.rollback()
        flash(f'物品删除失败，请稍后再试。错误信息: {e}', 'danger')
        app.logger.error(f"物品删除失败: {e}")
        return redirect(url_for('item_detail', item_id=item.id))


# --- 物品状态更新功能 (标记为已找回/已归还) ---
@app.route('/item/<int:item_id>/mark_resolved', methods=['POST'])
@login_required
def mark_item_resolved(item_id):
    """
    标记物品状态为已解决 (found/returned)。只接受 POST 请求。
    """
    item = Item.query.get_or_404(item_id)

    # 确保只有物品的发布者才能修改状态
    if item.author != current_user:
        flash('您无权修改此物品的状态。', 'danger')
        return redirect(url_for('dashboard'))

    # 如果已经是已解决状态，则不进行操作
    if item.status != 'active':
        flash('该物品已处于已解决状态。', 'info')
        return redirect(url_for('dashboard'))

    try:
        # 根据物品类型设置不同的解决状态
        if item.type == 'lost':
            item.status = 'found'  # 失物被找回
        elif item.type == 'found':
            item.status = 'returned'  # 拾物已归还

        db.session.commit()
        flash('物品状态已更新！', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        db.session.rollback()
        flash(f'物品状态更新失败，请稍后再试。错误信息: {e}', 'danger')
        app.logger.error(f"物品状态更新失败: {e}")
        return redirect(url_for('item_detail', item_id=item.id))


@app.route('/message/send/<int:receiver_id>/<int:item_id>', methods=['GET', 'POST'])
@app.route('/message/send/<int:receiver_id>', methods=['GET', 'POST']) # 不关联物品的私信
@login_required
def send_message(receiver_id, item_id=None):
    """
    发送私信的视图函数。
    GET 请求显示发送表单，POST 请求处理消息发送。
    """
    receiver = User.query.get_or_404(receiver_id)
    item = None
    if item_id:
        item = Item.query.get_or_404(item_id)

    # 不能给自己发消息
    if receiver.id == current_user.id:
        flash('您不能给自己发送消息。', 'danger')
        return redirect(url_for('index')) # 或者重定向到个人中心

    if request.method == 'POST':
        content = request.form.get('content')

        if not content or len(content.strip()) == 0:
            flash('消息内容不能为空！', 'danger')
            return redirect(request.url) # 返回当前页面

        new_message = Message(
            sender_id=current_user.id,
            receiver_id=receiver.id,
            item_id=item.id if item else None,
            content=content.strip()
        )
        db.session.add(new_message)
        try:
            db.session.commit()
            flash('消息发送成功！', 'success')
            # --- 新增：发送邮件提醒 ---
            # 确保 receiver 对象有 email 属性
            if receiver.email:
                send_email_notification(
                    to_email=receiver.email,
                    subject='校园失物招领：您有一条新消息！',
                    template_name='email_new_message.html',
                    receiver_username=receiver.username,
                    sender_username=current_user.username,
                    item_name=item.name if item else '无特定物品', # 如果有物品则传递物品名称
                    message_content=content.strip()
                )
            # --- 邮件提醒结束 ---
            # 成功发送后，可以跳转到消息列表或物品详情页
            if item:
                return redirect(url_for('item_detail', item_id=item.id))
            else:
                return redirect(url_for('my_messages')) # 跳转到我的消息
        except Exception as e:
            db.session.rollback()
            flash(f'消息发送失败，请稍后再试。错误: {e}', 'danger')
            app.logger.error(f"消息发送失败: {e}")
            return redirect(request.url)

    # GET 请求时，渲染发送消息的模板
    return render_template('send_message.html', receiver=receiver, item=item)


@app.route('/messages')
@login_required
def my_messages():
    """
    显示当前用户的收件箱和发件箱。
    """
    # 查询与当前用户相关的所有消息 (作为发送者或接收者)
    # 按时间降序排列，以显示最新消息在顶部
    messages = Message.query.filter(
        or_(Message.sender_id == current_user.id, Message.receiver_id == current_user.id)
    ).order_by(Message.timestamp.desc()).all()

    # 将未读消息标记为已读 (仅当用户是接收者时)
    # 这是一个简单的实现，更复杂的应用可能会在查看特定对话时才标记已读
    unread_messages = Message.query.filter_by(receiver_id=current_user.id, is_read=False).all()
    for msg in unread_messages:
        msg.is_read = True
    db.session.commit() # 提交已读状态更新

    return render_template('my_messages.html', messages=messages)

if __name__ == '__main__':
    # 运行 Flask 应用。
    # debug=True 模式适合开发环境，它会在代码修改时自动重载，并提供调试信息。
    # 生产环境中应关闭 debug 模式。
    app.run(debug=True)