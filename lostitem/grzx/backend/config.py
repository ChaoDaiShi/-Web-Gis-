import os

class Config:
    """应用配置类"""
    # 应用密钥，用于会话管理和CSRF保护
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # JWT密钥，用于生成和验证token
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    
    # JWT token过期时间（秒）
    JWT_ACCESS_TOKEN_EXPIRES = 86400

    # 使用 MySQL 数据库
    # 格式: mysql+pymysql://用户名:密码@主机:端口/数据库名
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:password@localhost:3306/user_center'
    
    # 禁用SQLAlchemy的修改跟踪，提高性能
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 头像上传目录
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'avatars')
    
    # 最大上传文件大小（5MB）
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    
    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # 邮件服务器配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.example.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    # 短信服务配置
    SMS_PROVIDER = os.environ.get('SMS_PROVIDER') or 'aliyun'
    ALIYUN_ACCESS_KEY = os.environ.get('ALIYUN_ACCESS_KEY')
    ALIYUN_ACCESS_SECRET = os.environ.get('ALIYUN_ACCESS_SECRET')
    ALIYUN_SIGN_NAME = os.environ.get('ALIYUN_SIGN_NAME') or '个人中心'
    ALIYUN_TEMPLATE_CODE = os.environ.get('ALIYUN_TEMPLATE_CODE')
