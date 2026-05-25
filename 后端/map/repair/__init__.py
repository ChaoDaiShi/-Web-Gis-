from flask import Blueprint
from .repair_category import repair_category_bp
from .repair_list import repair_list_bp
from .repair_operation import repair_operation_bp

repair_bp = Blueprint('repair', __name__)

repair_bp.register_blueprint(repair_category_bp)
repair_bp.register_blueprint(repair_list_bp)
repair_bp.register_blueprint(repair_operation_bp)

__all__ = ['repair_bp']
