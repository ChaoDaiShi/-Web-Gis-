from flask import Blueprint
from .config.map_config import map_config_bp
from .lost_item import lost_item_bp
from .repair import repair_bp

map_bp = Blueprint('map', __name__)

map_bp.register_blueprint(map_config_bp)
map_bp.register_blueprint(lost_item_bp)
map_bp.register_blueprint(repair_bp)

__all__ = ['map_bp']
