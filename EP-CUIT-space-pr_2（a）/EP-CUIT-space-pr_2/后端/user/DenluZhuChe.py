from flask import Flask, request, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import session
import os

# ================== 配置 ==================
class Config:
    SECRET_KEY = 'your-secret-key-here'

    #  你的数据库（已存在）
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://mapuser:123456@localhost/compus'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AMAP_WEB_KEY = '49382949a3128467653e88aab0daa5c7'
    AMAP_SECURITY_JS_CODE = '13aaa6de30599d02d3b3f1c562e9bd5e'

    # 管理员登录（可用环境变量覆盖，部署时请修改默认值）
    ADMIN_EMAIL = os.environ.get('CAMPUS_ADMIN_EMAIL', 'admin@campus.local')
    ADMIN_PASSWORD = os.environ.get('CAMPUS_ADMIN_PASSWORD', 'admin123')


# ================== 初始化 ==================
db = SQLAlchemy()


# ================== 模型 ==================
class User(db.Model):
    __tablename__ = 'user'   # 对应数据库表

    user_id = db.Column(db.Integer, primary_key=True)   # 对应 user_id
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    avatar_url = db.Column(db.String(500))
    bg_image = db.Column(db.String(500))
    signature = db.Column(db.String(255))
    bio = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"


# ================== Blueprint ==================
auth_bp = Blueprint('auth', __name__)


# ================== 注册 ==================
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

    # 检查用户名
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 400

    # 检查邮箱
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


# ================== 登录 ==================
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data:
        return jsonify({'message': 'No input data provided'}), 400

    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    # 去空格
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

    # 优先按邮箱查询，其次按用户名查询
    if email:
        user = User.query.filter_by(email=email).first()
    else:
        user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'Invalid username/email or password'}), 401

    try:
        # 安全验证
        if not check_password_hash(user.password_hash, password):
            return jsonify({'message': 'Invalid username/email or password'}), 401
    except Exception as e:
        # 防止历史脏数据（明文密码）
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


class Admin(db.Model):
    __tablename__ = 'admin'
    
    admin_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Admin {self.username}>"


# ================== 管理员登录 ==================
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


# ================== 修改密码 ==================
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


# ================== 重置密码（通过邮箱） ==================
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


# ================== 获取所有用户 ==================
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


# ================== 测试数据库 ==================
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


# ================== 应用工厂 ==================
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)

    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    return app


# ================== 启动 ==================
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5000)