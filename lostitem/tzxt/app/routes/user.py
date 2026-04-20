from flask import Blueprint, request, jsonify
from app.models.database import User, db

user_bp = Blueprint('users', __name__)

@user_bp.route('/', methods=['POST'])
def create_user():
    """
    创建新用户

    请求体 (JSON):
        username: 用户名（必需）
        email: 邮箱（必需）
        phone: 电话号码（可选）

    返回:
        成功消息和新创建的用户信息
    """
    data = request.get_json()

    if not data or not data.get('username') or not data.get('email'):
        return jsonify({'error': 'Missing required fields'}), 400

    existing_user = User.query.filter(
        (User.username == data['username']) | (User.email == data['email'])
    ).first()

    if existing_user:
        return jsonify({'error': 'User already exists'}), 400

    user = User(
        username=data['username'],
        email=data['email'],
        phone=data.get('phone', '')
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': 'User created successfully',
        'user': user.to_dict()
    }), 201

@user_bp.route('/', methods=['GET'])
def get_users():
    """
    获取所有用户列表

    返回:
        用户列表和总数
    """
    users = User.query.all()
    return jsonify({
        'users': [u.to_dict() for u in users],
        'total': len(users)
    })

@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    获取单个用户详情

    路径参数:
        user_id: 用户ID

    返回:
        用户详情或404错误
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'user': user.to_dict()})