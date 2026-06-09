from flask import Blueprint
from .lost_item_list import lost_item_list_bp
from .lost_item_publish import lost_item_publish_bp
from .lost_item_delete import lost_item_delete_bp
from .lost_item_status import lost_item_status_bp

lost_item_bp = Blueprint('lost_item', __name__)

lost_item_bp.register_blueprint(lost_item_list_bp)
lost_item_bp.register_blueprint(lost_item_publish_bp)
lost_item_bp.register_blueprint(lost_item_delete_bp)
lost_item_bp.register_blueprint(lost_item_status_bp)

__all__ = ['lost_item_bp']
