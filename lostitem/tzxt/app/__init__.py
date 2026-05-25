from flask import Flask
from flask_cors import CORS

def create_app():
    """
    Flask应用工厂函数
    创建并配置Flask应用实例，注册所有蓝图和数据库
    """
    app = Flask(__name__)
    CORS(app)

    # 配置SQLAlchemy数据库连接
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lostandfound.db'
    # 禁用SQLAlchemy的修改跟踪功能以提升性能
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # 设置Flask应用的密钥，用于会话加密
    app.config['SECRET_KEY'] = 'your-secret-key-here'

    # 初始化数据库
    from app.models.database import db
    db.init_app(app)

    # 导入所有路由蓝图
    from app.routes import notification_bp, lost_item_bp, claim_bp, user_bp

    # 注册蓝图，设置URL前缀
    # /api/notifications - 通知相关接口
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')
    # /api/lost-items - 失物相关接口
    app.register_blueprint(lost_item_bp, url_prefix='/api/lost-items')
    # /api/claims - 认领相关接口
    app.register_blueprint(claim_bp, url_prefix='/api/claims')
    # /api/users - 用户相关接口
    app.register_blueprint(user_bp, url_prefix='/api/users')

    # 在应用上下文中创建所有数据库表
    with app.app_context():
        db.create_all()

    return app