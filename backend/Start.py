from flask import Flask, send_from_directory, request, jsonify
from user.auth import auth_bp
from user.config import Config, db
from user.verify import verify_bp
from map.main import map_bp
from user.profile import profile_bp
from user.claim import claim_bp
from admin.admin_api import register_admin_routes
from message.main import message_bp
from nav.nav_api import nav_bp
from item import item_bp
from community import register_community_routes
from appointment.main import appointment_bp
from appointment.appointment_items import appointment_items_bp
import os

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'your_secret_key_123'
db.init_app(app)

try:
    from flask_cors import CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'], allow_headers=['Content-Type', 'Authorization'])
    print("CORS enabled via flask-cors")
except ImportError:
    print("Flask-CORS not found, using manual CORS handling")

@app.before_request
def handle_cors_preflight():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response

BACKEND_ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(BACKEND_ROOT)
STATIC_FOLDER = os.path.join(BACKEND_ROOT, 'static')
IMAGES_FOLDER = os.path.join(BACKEND_ROOT, 'images')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_FOLDER, filename)

@app.route('/images/<path:filename>')
def serve_images(filename):
    file_path = os.path.join(IMAGES_FOLDER, filename)
    if os.path.exists(file_path):
        return send_from_directory(IMAGES_FOLDER, filename)
    else:
        default_path = os.path.join(IMAGES_FOLDER, 'avatars', 'default.png')
        if os.path.exists(default_path):
            return send_from_directory(os.path.join(IMAGES_FOLDER, 'avatars'), 'default.png')
        return jsonify({'error': 'File not found'}), 404

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(verify_bp)
app.register_blueprint(map_bp, url_prefix="/api")
app.register_blueprint(profile_bp)
app.register_blueprint(claim_bp)
app.register_blueprint(nav_bp, url_prefix='/api/nav')
register_admin_routes(app)
app.register_blueprint(message_bp, url_prefix='/api')
app.register_blueprint(item_bp, url_prefix='/api')
register_community_routes(app)
app.register_blueprint(appointment_bp, url_prefix='/api')
app.register_blueprint(appointment_items_bp, url_prefix='/api')

@app.route('/test-route')
def test_route():
    return jsonify({'message': 'Test route works!'})

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
VUE_ROOT = os.path.join(PROJECT_ROOT, '前端', 'lost-found')
VUE_DIST = os.path.join(VUE_ROOT, 'dist')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    if os.path.exists(VUE_DIST):
        return send_from_directory(os.path.join(VUE_DIST, 'assets'), filename)
    return send_from_directory(os.path.join(VUE_ROOT, 'public'), filename)

@app.route('/favicon.ico')
def serve_favicon():
    if os.path.exists(VUE_DIST):
        return send_from_directory(VUE_DIST, 'favicon.ico')
    return send_from_directory(os.path.join(VUE_ROOT, 'public'), 'favicon.ico')

# 只处理根路径和静态资源，不拦截API路由
@app.route('/', methods=['GET', 'HEAD'])
def serve_vue_root():
    if os.path.exists(VUE_DIST):
        return send_from_directory(VUE_DIST, 'index.html')
    dev_index = os.path.join(VUE_ROOT, 'index.html')
    if os.path.exists(dev_index):
        return send_from_directory(VUE_ROOT, 'index.html')
    return {"message": "Vue front-end not built yet"}, 500

def run_initializations():
    import pymysql
    from werkzeug.security import generate_password_hash

    DB_CONFIG = {
        'host': 'localhost',
        'user': 'mapuser',
        'password': '123456',
        'database': 'compus',
        'charset': 'utf8mb4'
    }

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM admin WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            hashed = generate_password_hash('admin')
            cursor.execute("INSERT INTO admin (username, password_hash) VALUES (%s, %s)", ('admin', hashed))
            conn.commit()
            print("管理员账号初始化成功（admin/admin）")
        else:
            print("管理员账号已存在，跳过初始化")
    except Exception as e:
        print(f"管理员初始化失败: {e}")
        conn.rollback()

    try:
        cursor.execute("SELECT COUNT(*) FROM category")
        if cursor.fetchone()[0] == 0:
            categories = [('校园卡',), ('钥匙',), ('书包',), ('手机',), ('钱包',), ('证件',), ('文具',), ('其他',)]
            cursor.executemany("INSERT INTO category (name) VALUES (%s)", categories)
            conn.commit()
            print("分类数据初始化成功")
        else:
            print("分类数据已存在，跳过初始化")
    except Exception as e:
        print(f"分类初始化失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_initializations()
    print("启动统一后端服务：http://127.0.0.1:5000")
    app.run(debug=True, use_reloader=False, port=5000)