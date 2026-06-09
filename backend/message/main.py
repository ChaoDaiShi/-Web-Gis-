from flask import Blueprint
from .message_list import message_list_bp
from .message_read import message_read_bp
from .message_send import message_send_bp
from .message_delete import message_delete_bp

message_bp = Blueprint('message', __name__)

message_bp.register_blueprint(message_list_bp)
message_bp.register_blueprint(message_read_bp)
message_bp.register_blueprint(message_send_bp)
message_bp.register_blueprint(message_delete_bp)

__all__ = ['message_bp']
