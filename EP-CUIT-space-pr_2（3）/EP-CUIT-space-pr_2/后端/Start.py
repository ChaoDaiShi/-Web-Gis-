from flask import Flask, send_from_directory
from flask_cors import CORS
from DenluZhuChe import auth_bp, Config
from map_service import map_bp
from GeRenZhongXin import profile_bp
from admin_api import admin_api_bp
import os

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'your_secret_key_123'
CORS(app)

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(map_bp, url_prefix="/api")
app.register_blueprint(profile_bp)
app.register_blueprint(admin_api_bp, url_prefix='/api/admin')

BACKEND_ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(BACKEND_ROOT)
STATIC_FOLDER = os.path.join(BACKEND_ROOT, 'static')
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_FOLDER, filename)

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

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

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_vue(path):
    if path.startswith('api/'):
        return {"message": "API Not Found"}, 404

    if os.path.exists(VUE_DIST):
        asset_path = os.path.join(VUE_DIST, path)
        if path and os.path.exists(asset_path):
            return send_from_directory(VUE_DIST, path)
        return send_from_directory(VUE_DIST, 'index.html')

    dev_index = os.path.join(VUE_ROOT, 'index.html')
    if os.path.exists(dev_index):
        return send_from_directory(VUE_ROOT, 'index.html')
    return {"message": "Vue front-end not built yet"}, 500

with app.app_context():
    from DenluZhuChe import db
    db.init_app(app)

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