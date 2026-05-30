from flask import Blueprint
from user.auth import auth_bp
from user.profile import profile_bp
from user.claim import claim_bp

user_bp = Blueprint('user', __name__)

user_bp.register_blueprint(auth_bp, url_prefix='/api/auth')
user_bp.register_blueprint(profile_bp)
user_bp.register_blueprint(claim_bp)

__all__ = ['auth_bp', 'profile_bp', 'claim_bp']
