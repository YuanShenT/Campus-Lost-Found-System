# models.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import datetime # 导入 datetime 模块用于时间戳
# from datetime import datetime, timezone  # 导入 timezone 模块

db = SQLAlchemy()

# 保持 User 模型不变
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255)) # 确保这里是 255

    # 添加与 Item 模型的关系
    items = db.relationship('Item', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# --- 新增 Item 模型 ---
class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    # lost 或 found
    type = db.Column(db.String(10), nullable=False) # lost_item 或 found_item
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True) # 可以为空
    location = db.Column(db.String(200), nullable=False) # 丢失/拾取地点
    # 丢失/拾取时间，使用 datetime 类型
    event_time = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    image_file = db.Column(db.String(255), nullable=True, default='default.jpg') # 图片文件名，可为空

    # 外键：关联到发布该物品的用户ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 发布时间（创建记录的时间）
    posted_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    # 物品状态：例如 'active', 'found', 'returned'
    status = db.Column(db.String(20), nullable=False, default='active')
    # 定义 Item 和 User 之间的关系，让你可以通过 item.user 访问到发布者信息
    user = db.relationship('User', backref='items_posted')  # backref 会在 User 模型上创建一个 items_posted 属性
    pin_x = db.Column(db.Integer, nullable=True)  # 图钉X坐标
    pin_y = db.Column(db.Integer, nullable=True)  # 图钉Y坐标
    def __repr__(self):
        return f'<Item {self.name} - {self.type}>'

# 新增 Message 模型
class Message(db.Model):
    __tablename__ = 'messages' # 建议为表指定一个明确的名称
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id')) # 消息关联的物品，可为空
    content = db.Column(db.Text, nullable=False)
    # timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # ... (在 Message 类内部) ...
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    # 定义与 User 和 Item 的关系
    # sender 是发送方用户对象
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy=True))
    # receiver 是接收方用户对象
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref=db.backref('received_messages', lazy=True))
    # item 是关联的物品对象
    item = db.relationship('Item', backref=db.backref('messages', lazy=True))

    def __repr__(self):
        return f'<Message {self.id} from {self.sender_id} to {self.receiver_id} about Item {self.item_id}>'
