from admin.admin_table_api import table_bp as admin_table_api_bp
from admin.admin_return_api import admin_return_api_bp
from admin.admin_claim_api import admin_claim_api_bp
from admin.admin_verify_api import admin_verify_bp
from admin.admin_category_api import admin_category_api_bp
from admin.admin_item_api import admin_item_api_bp
from admin.admin_statistics_api import admin_statistics_api_bp
from admin.admin_user_api import admin_user_api_bp
from admin.admin_config_api import admin_config_api_bp
from admin.admin_repair_api import admin_repair_api_bp
from admin.admin_admin_api import admin_admin_api_bp
from admin.admin_audit_api import admin_audit_bp

def register_admin_routes(app):
    app.register_blueprint(admin_table_api_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_return_api_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_claim_api_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_verify_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_category_api_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_item_api_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_statistics_api_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_user_api_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_config_api_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_repair_api_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_admin_api_bp, url_prefix='/api/admin')
    app.register_blueprint(admin_audit_bp, url_prefix='/api/admin/audit')
