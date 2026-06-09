from flask import Blueprint
from .appointment_create import appointment_create_bp
from .appointment_list import appointment_list_bp
from .appointment_update import appointment_update_bp
from .appointment_detail import appointment_detail_bp
from .appointment_items import appointment_items_bp

appointment_bp = Blueprint('appointment', __name__)

appointment_bp.register_blueprint(appointment_create_bp)
appointment_bp.register_blueprint(appointment_list_bp)
appointment_bp.register_blueprint(appointment_update_bp)
appointment_bp.register_blueprint(appointment_detail_bp)
appointment_bp.register_blueprint(appointment_items_bp)

__all__ = ['appointment_bp']
