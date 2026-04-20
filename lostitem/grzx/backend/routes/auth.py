from flask import Blueprint, request, jsonify
from models import User, db
from utils.validators import create_token, token_required

# 创建认证相关的蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册接口
    
    请求参数:
        email: 邮箱
        password: 密码
        username: 用户名
    
    返回:
        成功: {"success": true, "message": "注册成功", "data": {"token": "...", "user": {...}}}
        失败: {"success": false, "message": "错误信息"}
    """
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': '请求数据无效'}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    username = data.get('username', '').strip()

    if not email or not password or not username:
        return jsonify({'success': False, 'message': '邮箱、密码和用户名不能为空'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': '该邮箱已被注册'}), 409

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': '该用户名已被使用'}), 409

    if len(password) < 6:
        return jsonify({'success': False, 'message': '密码长度不能少于6位'}), 400

    # 创建新用户
    user = User(email=email, username=username)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # 生成token
    token = create_token(user.id)

    return jsonify({
        'success': True,
        'message': '注册成功',
        'data': {
            'token': token,
            'user': user.to_dict()
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录接口
    
    请求参数:
        email: 邮箱
        password: 密码
    
    返回:
        成功: {"success": true, "message": "登录成功", "data": {"token": "...", "user": {...}}}
        失败: {"success": false, "message": "错误信息"}
    """
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': '请求数据无效'}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'message': '邮箱和密码不能为空'}), 400

    # 查找用户
    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': '邮箱或密码错误'}), 401

    # 生成token
    token = create_token(user.id)

    return jsonify({
        'success': True,
        'message': '登录成功',
        'data': {
            'token': token,
            'user': user.to_dict()
        }
    })

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """获取当前用户信息接口
    
    返回:
        {"success": true, "data": {"user": {...}}}
    """
    return jsonify({
        'success': True,
        'data': current_user.to_dict()
    })
