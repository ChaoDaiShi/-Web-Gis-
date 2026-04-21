from flask import Flask, redirect
from flask_cors import CORS
from DenluZhuChe import auth_bp, Config
from map_service import map_bp

# 创建主应用
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# 注册蓝图
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(map_bp)

# 添加登录界面跳转路由
@app.route('/login')
def login_redirect():
    # 重定向到前端的登录界面
    return redirect('http://127.0.0.1:5000/')

# 确保数据库初始化
with app.app_context():
    # 从DenluZhuChe导入db并初始化
    from DenluZhuChe import db
    db.init_app(app)
    # 注意：这里不自动创建表，因为表结构应该已经存在

if __name__ == "__main__":
    print("启动统一后端服务：http://127.0.0.1:5000")
    app.run(
        debug=True,
        use_reloader=False,   # ⭐ 关键修复
        port=5000
    )