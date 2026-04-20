from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from app.config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    CORS(app)
    db.init_app(app)
    
    from app.auth import views as auth_views
    app.register_blueprint(auth_views.auth_bp, url_prefix='/api/auth')
    
    with app.app_context():
        db.create_all()
    
    return app