# config.py
import os

class Config:
    # 你的 MySQL 数据库连接 URI
    # 格式: mysql+pymysql://用户名:密码@主机/数据库名
    # 请务必将 'your_mysql_password' 替换为你的实际 MySQL 密码
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost/lost_and_found'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SECRET_KEY 用于 Flask 会话、CSRF 保护等。
    # 在生产环境中，强烈建议使用更复杂且难以猜测的字符串，并从环境变量中获取。
    # 例如：os.environ.get('SECRET_KEY')
    SECRET_KEY = os.urandom(24).hex() # 随机生成一个24字节的十六进制字符串