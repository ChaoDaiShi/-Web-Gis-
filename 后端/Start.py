from flask import Flask, send_from_directory
from flask_cors import CORS
from DenluZhuChe import auth_bp, Config
from map_service import map_bp
import os

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'your_secret_key_123'
CORS(app)

# ================= 注册接口 =================
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(map_bp, url_prefix="/api")

# ================= 前端目录路径（Vue） =================
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


# ================= 数据库初始化 =================
with app.app_context():
    from DenluZhuChe import db
    db.init_app(app)


if __name__ == "__main__":
    print("启动统一后端服务：http://127.0.0.1:5000")
    app.run(debug=True, use_reloader=False, port=5000)