from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from models import db
from routes import auth_bp, profile_bp, password_bp, phone_bp

def create_app(config_class=Config):
    """创建Flask应用实例
    
    Args:
        config_class: 配置类
    
    Returns:
        Flask应用实例
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 配置CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 初始化数据库
    db.init_app(app)

    # 注册路由蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(password_bp)
    app.register_blueprint(phone_bp)

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """健康检查接口"""
        return jsonify({'success': True, 'message': 'Service is running'})

    # 创建数据库表
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    """主函数"""
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
