import random
import string
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from models import User, VerificationCode, db
import jwt

def generate_verification_code(length=6):
    """生成指定长度的验证码"""
    return ''.join(random.choices(string.digits, k=length))

def create_verification(email=None, phone=None, code_type='email', expires_minutes=10):
    """创建验证码并保存到数据库
    
    Args:
        email: 邮箱地址
        phone: 手机号
        code_type: 验证码类型
        expires_minutes: 过期时间（分钟）
    
    Returns:
        生成的验证码
    """
    code = generate_verification_code()
    expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)

    # 查找同类型的未使用验证码并标记为已使用
    existing = VerificationCode.query.filter(
        ((email and VerificationCode.email == email) or (phone and VerificationCode.phone == phone)),
        VerificationCode.type == code_type,
        VerificationCode.used == False
    ).first()

    if existing:
        existing.used = True
        db.session.commit()

    # 创建新的验证码记录
    verification = VerificationCode(
        email=email,
        phone=phone,
        code=code,
        type=code_type,
        expires_at=expires_at
    )
    db.session.add(verification)
    db.session.commit()

    return code

def verify_code(email=None, phone=None, code=None, code_type='email'):
    """验证验证码
    
    Args:
        email: 邮箱地址
        phone: 手机号
        code: 验证码
        code_type: 验证码类型
    
    Returns:
        (是否有效, 消息)
    """
    if not code:
        return False, '验证码不能为空'

    # 查找最新的未使用验证码
    verification = VerificationCode.query.filter(
        ((email and VerificationCode.email == email) or (phone and VerificationCode.phone == phone)),
        VerificationCode.code == code,
        VerificationCode.type == code_type,
        VerificationCode.used == False
    ).order_by(VerificationCode.created_at.desc()).first()

    if not verification:
        return False, '验证码无效'

    if not verification.is_valid():
        return False, '验证码已过期'

    # 标记验证码为已使用
    verification.used = True
    db.session.commit()

    return True, '验证成功'

def create_token(user_id):
    """生成JWT token
    
    Args:
        user_id: 用户ID
    
    Returns:
        生成的token
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

def decode_token(token):
    """解码JWT token
    
    Args:
        token: JWT token
    
    Returns:
        用户ID或None
    """
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """JWT token认证装饰器
    
    用于保护需要认证的API接口
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # 从请求头获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'success': False, 'message': '缺少认证令牌'}), 401

        # 验证token
        user_id = decode_token(token)
        if not user_id:
            return jsonify({'success': False, 'message': '令牌无效或已过期'}), 401

        # 获取用户信息
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 401

        # 将用户对象传递给被装饰的函数
        return f(user, *args, **kwargs)

    return decorated

def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否允许
    
    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名集合
    
    Returns:
        是否允许
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
