from flask import Blueprint, request, jsonify
from app.models.database import LostItem, User, db
from app.services.notification_service import NotificationService

lost_item_bp = Blueprint('lost_items', __name__)

@lost_item_bp.route('/', methods=['POST'])
def create_lost_item():
    """
    创建新的失物发布

    请求体 (JSON):
        title: 失物标题（必需）
        location: 丢失地点（必需）
        owner_id: 失主用户ID（必需）
        description: 失物描述（可选）
        category: 失物类别（可选）

    返回:
        成功消息和新创建的失物信息
    """
    data = request.get_json()

    if not data or not data.get('title') or not data.get('location') or not data.get('owner_id'):
        return jsonify({'error': 'Missing required fields'}), 400

    owner = User.query.get(data['owner_id'])
    if not owner:
        return jsonify({'error': 'Owner not found'}), 404

    lost_item = LostItem(
        title=data['title'],
        description=data.get('description', ''),
        location=data['location'],
        category=data.get('category', ''),
        owner_id=data['owner_id'],
        status='lost'
    )

    db.session.add(lost_item)
    db.session.commit()

    NotificationService.notify_lost_item_published(lost_item.id, lost_item.owner_id)

    return jsonify({
        'message': 'Lost item created successfully',
        'lost_item': lost_item.to_dict()
    }), 201

@lost_item_bp.route('/', methods=['GET'])
def get_lost_items():
    """
    获取失物列表

    查询参数:
        status: 过滤状态（可选），如 'lost' 或 'claimed'
        category: 过滤类别（可选）

    返回:
        失物列表和总数
    """
    status = request.args.get('status')
    category = request.args.get('category')

    query = LostItem.query
    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)

    lost_items = query.order_by(LostItem.created_at.desc()).all()
    return jsonify({
        'lost_items': [item.to_dict() for item in lost_items],
        'total': len(lost_items)
    })

@lost_item_bp.route('/<int:item_id>', methods=['GET'])
def get_lost_item(item_id):
    """
    获取单个失物详情

    路径参数:
        item_id: 失物ID

    返回:
        失物详情或404错误
    """
    lost_item = LostItem.query.get(item_id)
    if not lost_item:
        return jsonify({'error': 'Lost item not found'}), 404

    return jsonify({'lost_item': lost_item.to_dict()})

@lost_item_bp.route('/<int:item_id>', methods=['PUT'])
def update_lost_item(item_id):
    """
    更新失物信息

    路径参数:
        item_id: 失物ID

    请求体 (JSON):
        title: 失物标题（可选）
        description: 失物描述（可选）
        location: 丢失地点（可选）
        category: 失物类别（可选）
        status: 状态（可选）

    返回:
        成功消息和更新后的失物信息
    """
    lost_item = LostItem.query.get(item_id)
    if not lost_item:
        return jsonify({'error': 'Lost item not found'}), 404

    data = request.get_json()
    if data.get('title'):
        lost_item.title = data['title']
    if data.get('description'):
        lost_item.description = data['description']
    if data.get('location'):
        lost_item.location = data['location']
    if data.get('category'):
        lost_item.category = data['category']
    if data.get('status'):
        lost_item.status = data['status']

    db.session.commit()
    return jsonify({
        'message': 'Lost item updated successfully',
        'lost_item': lost_item.to_dict()
    })

@lost_item_bp.route('/<int:item_id>', methods=['DELETE'])
def delete_lost_item(item_id):
    """
    删除失物记录

    路径参数:
        item_id: 失物ID

    返回:
        成功消息
    """
    lost_item = LostItem.query.get(item_id)
    if not lost_item:
        return jsonify({'error': 'Lost item not found'}), 404

    db.session.delete(lost_item)
    db.session.commit()
    return jsonify({'message': 'Lost item deleted successfully'})