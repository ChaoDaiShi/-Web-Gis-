from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

# 初始化SQLAlchemy对象
db = SQLAlchemy()

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'  # 表名

    # 主键
    id = db.Column(db.Integer, primary_key=True)
    # 邮箱（唯一，非空，建立索引）
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    # 手机号（唯一，可为空）
    phone = db.Column(db.String(20), unique=True, nullable=True)
    # 用户名（唯一，非空）
    username = db.Column(db.String(80), unique=True, nullable=False)
    # 密码哈希值（非空）
    password_hash = db.Column(db.String(255), nullable=False)
    # 头像路径（默认值为default.png）
    avatar = db.Column(db.String(255), default='default.png')
    # 用户签名（默认值为空字符串）
    signature = db.Column(db.String(255), default='')
    # 个人介绍（默认值为空字符串）
    bio = db.Column(db.Text, default='')
    # 创建时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 更新时间（自动更新）
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        """设置密码（生成哈希值）"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """将用户对象转换为字典"""
        return {
            'id': self.id,
            'email': self.email,
            'phone': self.phone,
            'username': self.username,
            'avatar': f'/static/avatars/{self.avatar}' if not self.avatar.startswith('http') else self.avatar,
            'signature': self.signature,
            'bio': self.bio,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class VerificationCode(db.Model):
    """验证码模型"""
    __tablename__ = 'verification_codes'  # 表名

    # 主键
    id = db.Column(db.Integer, primary_key=True)
    # 邮箱（可为空）
    email = db.Column(db.String(120), nullable=False, index=True)
    # 手机号（可为空）
    phone = db.Column(db.String(20), nullable=False, index=True)
    # 验证码
    code = db.Column(db.String(10), nullable=False)
    # 验证码类型（如email、phone等）
    type = db.Column(db.String(20), nullable=False)
    # 过期时间
    expires_at = db.Column(db.DateTime, nullable=False)
    # 是否已使用
    used = db.Column(db.Boolean, default=False)
    # 创建时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self):
        """检查验证码是否有效"""
        return not self.used and datetime.utcnow() < self.expires_at
