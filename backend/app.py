from flask import Flask, send_from_directory, request, jsonify, session
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
application = app

app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_secret_key_123')

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

# ==================== 系统操作日志记录 ====================
LOG_IGNORE_PREFIXES = ('/static/', '/images/', '/favicon.ico')

@app.after_request
def log_api_call(response):
    """自动记录所有API调用到system_logs表"""
    try:
        path = request.path
        method = request.method
        
        # 跳过静态资源
        if any(path.startswith(p) for p in LOG_IGNORE_PREFIXES):
            return response
        
        # 只记录写操作和关键读操作
        if method in ('POST', 'PUT', 'DELETE'):
            from utils.logger import auto_log
            import threading
            
            user_id = session.get('user_id') or session.get('user') or session.get('admin_id')
            action = f"{method} {path}"
            detail = f"状态码: {response.status_code}"
            ip = request.remote_addr
            
            # 异步记录避免阻塞响应
            def _log():
                from utils.logger import log_action
                log_action(user_id, action, detail=detail, ip_address=ip)
            
            t = threading.Thread(target=_log)
            t.daemon = True
            t.start()
    except Exception as e:
        pass  # 日志失败不影响业务
    
    return response
# ==================== 日志记录结束 ====================

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

def register_routes():
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
    from appointment.return_appointment import return_appointment_bp
    from user.friend import friend_bp
    from user.chat import chat_bp
    from user.user_search import user_search_bp
    from user.user_profile import user_profile_bp
    
    app.config.from_object(Config)
    db.init_app(app)
    
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
    app.register_blueprint(return_appointment_bp, url_prefix='/api')
    app.register_blueprint(friend_bp, url_prefix='/api')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(user_search_bp, url_prefix='/api')
    app.register_blueprint(user_profile_bp, url_prefix='/api')

register_routes()

@app.route('/test-route')
def test_route():
    return jsonify({'message': 'Test route works!'})

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
VUE_ROOT = os.path.join(PROJECT_ROOT, 'frontend')
VUE_DIST = os.path.join(VUE_ROOT, 'dist')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    assets_path = os.path.join(VUE_DIST, 'assets')
    if os.path.exists(assets_path):
        return send_from_directory(assets_path, filename)
    return send_from_directory(os.path.join(VUE_ROOT, 'public'), filename)

@app.route('/favicon.ico')
def serve_favicon():
    if os.path.exists(VUE_DIST):
        favicon_path = os.path.join(VUE_DIST, 'favicon.ico')
        if os.path.exists(favicon_path):
            return send_from_directory(VUE_DIST, 'favicon.ico')
    return send_from_directory(os.path.join(VUE_ROOT, 'public'), 'favicon.ico')

@app.route('/', methods=['GET', 'HEAD'])
@app.route('/<path:path>', methods=['GET', 'HEAD'])
def serve_vue_app(path=None):
    index_path = os.path.join(VUE_DIST, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(VUE_DIST, 'index.html')
    return jsonify({"message": "Vue front-end not built yet"}), 500

def run_initializations():
    import pymysql
    from common.db_config import DB_CONFIG, get_conn
    from werkzeug.security import generate_password_hash

    try:
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
    except Exception as e:
        print(f"⚠️  数据库连接失败，跳过初始化: {e}")
        print("💡 提示：请检查以下内容：")
        print("   1. 云数据库安全组是否允许您的IP访问")
        print("   2. 网络连接是否正常")
        print("   3. 数据库账号密码是否正确")
        print("   4. 可临时使用本地数据库进行开发")

if __name__ == "__main__":
    run_initializations()
    print("启动统一后端服务：http://127.0.0.1:5000")
    app.run(debug=True, use_reloader=False, port=5000)