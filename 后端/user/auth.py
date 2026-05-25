from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from user.models import User, Admin
from user.config import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data:
        return jsonify({'message': 'No input data provided'}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Missing required fields'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 400

    if email and User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already exists'}), 400

    hashed_password = generate_password_hash(password)

    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_password
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User created successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data:
        return jsonify({'message': 'No input data provided'}), 400

    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if email:
        email = email.strip()
    if username:
        username = username.strip()
    if password:
        password = password.strip()

    if not password:
        return jsonify({'message': 'Missing required fields'}), 400

    if not email and not username:
        return jsonify({'message': 'Missing required fields'}), 400

    if email:
        user = User.query.filter_by(email=email).first()
    else:
        user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'Invalid username/email or password'}), 401

    try:
        if not check_password_hash(user.password_hash, password):
            return jsonify({'message': 'Invalid username/email or password'}), 401
    except Exception as e:
        if user.password_hash != password:
            return jsonify({'message': 'Invalid username/email or password'}), 401
        
    session['user'] = user.user_id

    return jsonify({
        'message': 'Login successful',
        'user': {
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email
        }
    }), 200


@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No input data provided'}), 400

    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    if not username or not password:
        return jsonify({'message': '请输入用户名和密码'}), 400

    admin = Admin.query.filter_by(username=username).first()
    
    if not admin:
        return jsonify({'message': '用户名或密码错误'}), 401

    try:
        if check_password_hash(admin.password_hash, password):
            return jsonify({'message': '管理员登录成功', 'admin': True}), 200
    except Exception as e:
        if admin.password_hash == password:
            return jsonify({'message': '管理员登录成功', 'admin': True}), 200

    return jsonify({'message': '用户名或密码错误'}), 401


@auth_bp.route('/change-email', methods=['POST'])
def change_email():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'No input data provided'}), 400
    
    user_id = data.get('user_id')
    password = data.get('password')
    new_email = data.get('new_email')
    
    if not user_id or not password or not new_email:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 400
    
    try:
        if not check_password_hash(user.password_hash, password):
            return jsonify({'success': False, 'message': '密码不正确'}), 400
    except Exception as e:
        if user.password_hash != password:
            return jsonify({'success': False, 'message': '密码不正确'}), 400
    
    existing_user = User.query.filter_by(email=new_email).first()
    if existing_user and existing_user.user_id != user.user_id:
        return jsonify({'success': False, 'message': '该邮箱已被注册'}), 400
    
    user.email = new_email
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': '邮箱修改成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'No input data provided'}), 400
    
    user_id = data.get('user_id')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not user_id or not old_password or not new_password:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 400
    
    try:
        if not check_password_hash(user.password_hash, old_password):
            return jsonify({'success': False, 'message': '原密码不正确'}), 400
    except Exception as e:
        if user.password_hash != old_password:
            return jsonify({'success': False, 'message': '原密码不正确'}), 400
    
    user.password_hash = generate_password_hash(new_password)
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': '密码修改成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'No input data provided'}), 400
    
    email = data.get('email')
    new_password = data.get('new_password')
    
    if not email or not new_password:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'success': False, 'message': '该邮箱未注册'}), 400
    
    user.password_hash = generate_password_hash(new_password)
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': '密码重置成功，请使用新密码登录'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@auth_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()

    result = []
    for user in users:
        result.append({
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "create_time": user.create_time
        })

    return jsonify(result), 200


@auth_bp.route('/test_db')
def test_db():
    try:
        users = User.query.all()
        return jsonify({
            "status": "success",
            "count": len(users)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
