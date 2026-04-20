from flask import Blueprint, request, jsonify
from app.services.notification_service import NotificationService
from app.models.database import Notification, db

notification_bp = Blueprint('notifications', __name__)

@notification_bp.route('/', methods=['GET'])
def get_notifications():
    """
    获取用户通知列表

    查询参数:
        user_id: 用户ID（必需）
        unread_only: 是否只返回未读通知，可选值：true/false

    返回:
        包含通知列表和总数的JSON响应
    """
    user_id = request.args.get('user_id', type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'

    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    notifications = NotificationService.get_user_notifications(user_id, unread_only)
    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'total': len(notifications)
    })

@notification_bp.route('/<int:notification_id>/read', methods=['PUT'])
def mark_notification_read(notification_id):
    """
    将单条通知标记为已读

    路径参数:
        notification_id: 通知ID

    返回:
        成功消息或错误响应
    """
    success = NotificationService.mark_as_read(notification_id)
    if success:
        return jsonify({'message': 'Notification marked as read'})
    return jsonify({'error': 'Notification not found'}), 404

@notification_bp.route('/read-all', methods=['PUT'])
def mark_all_notifications_read():
    """
    将用户的所有通知标记为已读

    查询参数:
        user_id: 用户ID（必需）

    返回:
        成功消息或错误响应
    """
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    NotificationService.mark_all_as_read(user_id)
    return jsonify({'message': 'All notifications marked as read'})