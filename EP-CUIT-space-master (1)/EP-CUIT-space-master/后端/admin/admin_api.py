from admin.admin_common import get_conn, admin_required, send_claim_notification, send_return_notification
from admin.admin_user_api import admin_user_api_bp
from admin.admin_item_api import admin_item_api_bp
from admin.admin_claim_api import admin_claim_api_bp
from admin.admin_return_api import admin_return_api_bp
from admin.admin_category_api import admin_category_api_bp
from admin.admin_statistics_api import admin_statistics_api_bp
from admin.admin_verify_api import admin_verify_bp

def register_admin_routes(app):
    app.register_blueprint(admin_user_api_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_item_api_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_claim_api_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_return_api_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_category_api_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_statistics_api_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_verify_bp, url_prefix='/api/admin')

__all__ = [
    'admin_user_api_bp',
    'admin_item_api_bp',
    'admin_claim_api_bp',
    'admin_return_api_bp',
    'admin_category_api_bp',
    'admin_statistics_api_bp',
    'admin_verify_bp',
    'register_admin_routes',
    'get_conn',
    'admin_required',
    'send_claim_notification',
    'send_return_notification'
]