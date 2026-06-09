from flask import Blueprint
from .posts import posts_bp
from .likes import likes_bp
from .comments import comments_bp
from .notifications import notifications_bp
from .tags import tags_bp
from .follows import follows_bp

community_bp = Blueprint('community', __name__)

def register_community_routes(app):
    app.register_blueprint(posts_bp, url_prefix='/api/community')
    app.register_blueprint(likes_bp, url_prefix='/api/community')
    app.register_blueprint(comments_bp, url_prefix='/api/community')
    app.register_blueprint(notifications_bp, url_prefix='/api/community')
    app.register_blueprint(tags_bp, url_prefix='/api/community')
    app.register_blueprint(follows_bp, url_prefix='/api/community')
    
    return community_bp
