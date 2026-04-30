from flask import Flask, request, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import session

# ================== 配置 ==================
class Config:
    SECRET_KEY = 'your-secret-key-here'

    #  你的数据库（已存在）
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://mapuser:123456@localhost/compus'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AMAP_WEB_KEY = '49382949a3128467653e88aab0daa5c7'
    AMAP_SECURITY_JS_CODE = '13aaa6de30599d02d3b3f1c562e9bd5e'


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
    password = data.get('password')

    # 去空格
    if email:
        email = email.strip()
    if password:
        password = password.strip()

    if not email or not password:
        return jsonify({'message': 'Missing required fields'}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({'message': 'Invalid email or password'}), 401

    try:
        # 安全验证
        if not check_password_hash(user.password_hash, password):
            return jsonify({'message': 'Invalid email or password'}), 401
    except Exception as e:
        # 防止历史脏数据（明文密码）
        if user.password_hash != password:
            return jsonify({'message': 'Invalid email or password'}), 401
        
    session['user'] = user.user_id

    return jsonify({
        'message': 'Login successful',
        'user': {
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email
        }
    }), 200


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