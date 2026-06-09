from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
import math
from user.models import User
from models import LostItem, ItemCategory, SystemLog
from user.config import db

item_bp = Blueprint('item', __name__)

def log_action(user_id, action, target_type, target_id, detail, ip_address):
    log = SystemLog(
        user_id=str(user_id),
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        detail=detail,
        ip_address=ip_address
    )
    db.session.add(log)
    db.session.commit()

def get_user_id_from_token():
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return None
    
    token = auth[7:]
    if token.startswith('user_'):
        return token[5:]
    return None

@item_bp.route('/api/items', methods=['GET'])
def get_items():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    keyword = request.args.get('keyword', '')
    category_id = request.args.get('category_id', type=int)
    status = request.args.get('status', '')
    item_type = request.args.get('item_type', '')
    
    query = LostItem.query.filter_by(audit_status='approved')
    
    if keyword:
        query = query.filter(
            db.or_(
                LostItem.title.contains(keyword),
                LostItem.description.contains(keyword),
                LostItem.location_name.contains(keyword)
            )
        )
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if item_type:
        query = query.filter_by(item_type=item_type)
    
    query = query.order_by(LostItem.publish_time.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    items = [item.to_dict() for item in pagination.items]
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'items': items,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })

@item_bp.route('/api/items/<item_id>', methods=['GET'])
def get_item(item_id):
    item = LostItem.query.filter_by(item_id=int(item_id), audit_status='approved').first()
    if not item:
        return jsonify({'code': 404, 'message': '物品不存在或未通过审核'}), 404
    
    item.view_count += 1
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': item.to_dict()
    })

@item_bp.route('/api/items', methods=['POST'])
def create_item():
    current_user_id = get_user_id_from_token()
    if not current_user_id:
        return jsonify({'code': 401, 'message': '未授权'}), 401
    
    data = request.get_json()
    
    required_fields = ['title', 'description']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'code': 400, 'message': f'{field}不能为空'}), 400
    
    item = LostItem(
        title=data['title'],
        description=data['description'],
        category_id=data.get('category_id'),
        item_type=data.get('item_type', 'lost'),
        location_name=data.get('location_name'),
        longitude=data.get('longitude'),
        latitude=data.get('latitude'),
        contact_info=data.get('contact_info'),
        image_url=data.get('image_url'),
        publisher_id=int(current_user_id),
        status='pending',
        audit_status='pending'
    )
    
    db.session.add(item)
    db.session.commit()
    
    log_action(
        user_id=current_user_id,
        action='create_item',
        target_type='lost_item',
        target_id=item.item_id,
        detail=f'发布物品: {item.title}',
        ip_address=request.remote_addr
    )
    
    return jsonify({
        'code': 201,
        'message': '发布成功，等待审核',
        'data': item.to_dict()
    }), 201

@item_bp.route('/api/items/<item_id>', methods=['PUT'])
def update_item(item_id):
    current_user_id = get_user_id_from_token()
    if not current_user_id:
        return jsonify({'code': 401, 'message': '未授权'}), 401
    
    item = LostItem.query.get(int(item_id))
    
    if not item:
        return jsonify({'code': 404, 'message': '物品不存在'}), 404
    
    if item.publisher_id != int(current_user_id):
        return jsonify({'code': 403, 'message': '无权限修改此物品'}), 403
    
    data = request.get_json()
    
    if 'title' in data:
        item.title = data['title']
    if 'description' in data:
        item.description = data['description']
    if 'category_id' in data:
        item.category_id = data['category_id']
    if 'item_type' in data:
        item.item_type = data['item_type']
    if 'location_name' in data:
        item.location_name = data['location_name']
    if 'longitude' in data:
        item.longitude = data['longitude']
    if 'latitude' in data:
        item.latitude = data['latitude']
    if 'contact_info' in data:
        item.contact_info = data['contact_info']
    if 'image_url' in data:
        item.image_url = data['image_url']
    
    item.updated_at = datetime.utcnow()
    db.session.commit()
    
    log_action(
        user_id=current_user_id,
        action='update_item',
        target_type='lost_item',
        target_id=item.item_id,
        detail=f'更新物品: {item.title}',
        ip_address=request.remote_addr
    )
    
    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': item.to_dict()
    })

@item_bp.route('/api/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    current_user_id = get_user_id_from_token()
    if not current_user_id:
        return jsonify({'code': 401, 'message': '未授权'}), 401
    
    item = LostItem.query.get(int(item_id))
    
    if not item:
        return jsonify({'code': 404, 'message': '物品不存在'}), 404
    
    if item.publisher_id != int(current_user_id):
        return jsonify({'code': 403, 'message': '无权限删除此物品'}), 403
    
    item_title = item.title
    item_id_value = item.item_id
    db.session.delete(item)
    db.session.commit()
    
    log_action(
        user_id=current_user_id,
        action='delete_item',
        target_type='lost_item',
        target_id=item_id_value,
        detail=f'删除物品: {item_title}',
        ip_address=request.remote_addr
    )
    
    return jsonify({
        'code': 200,
        'message': '删除成功'
    })

@item_bp.route('/api/items/my', methods=['GET'])
def get_my_items():
    current_user_id = get_user_id_from_token()
    if not current_user_id:
        return jsonify({'code': 401, 'message': '未授权'}), 401
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', '')
    
    query = LostItem.query.filter_by(publisher_id=int(current_user_id))
    
    if status:
        query = query.filter_by(status=status)
    
    query = query.order_by(LostItem.publish_time.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    items = [item.to_dict() for item in pagination.items]
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'items': items,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })

@item_bp.route('/api/items/categories', methods=['GET'])
def get_categories():
    categories = ItemCategory.query.filter_by(is_active=True).order_by(ItemCategory.sort_order).all()
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': [cat.to_dict() for cat in categories]
    })

@item_bp.route('/api/items/<item_id>/claim', methods=['POST'])
def claim_item(item_id):
    current_user_id = get_user_id_from_token()
    if not current_user_id:
        return jsonify({'code': 401, 'message': '未授权'}), 401
    
    item = LostItem.query.get(int(item_id))
    
    if not item:
        return jsonify({'code': 404, 'message': '物品不存在'}), 404
    
    if item.status != 'pending':
        return jsonify({'code': 400, 'message': '该物品不可认领'}), 400
    
    # 使用 raw SQL 检查是否已有认领记录（claim 表已合并到 claim_form）
    from common.db_config import get_conn

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT claim_id FROM claim_form WHERE item_id = %s AND user_id = %s LIMIT 1",
        (int(item_id), int(current_user_id))
    )
    existing = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if existing:
        return jsonify({'code': 400, 'message': '您已申请认领此物品'}), 400
    
    data = request.get_json()
    
    conn = get_conn()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        INSERT INTO claim_form (item_id, user_id, claim_reason, status, create_time)
        VALUES (%s, %s, %s, 0, %s)
    """, (int(item_id), int(current_user_id), data.get('claim_reason'), now))
    claim_id = cursor.lastrowid
    
    # 同步创建 audit 统一审核记录
    cursor.execute("""
        INSERT INTO audit (target_type, target_id, requester_id, status, create_time, update_time)
        VALUES ('claim_form', %s, %s, 'pending', %s, %s)
    """, (claim_id, int(current_user_id), now, now))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    log_action(
        user_id=current_user_id,
        action='claim_item',
        target_type='claim_record',
        target_id=claim_id,
        detail=f'申请认领物品: {item.title}',
        ip_address=request.remote_addr
    )
    
    return jsonify({
        'code': 201,
        'message': '认领申请已提交，等待审核',
        'data': claim.to_dict()
    }), 201

@item_bp.route('/api/items/nearby', methods=['GET'])
def get_nearby_items():
    longitude = request.args.get('longitude', type=float)
    latitude = request.args.get('latitude', type=float)
    distance = request.args.get('distance', 1000, type=int)
    
    if not longitude or not latitude:
        return jsonify({'code': 400, 'message': '缺少经纬度参数'}), 400
    
    lat_range = distance / 111000
    
    lat_rad = math.radians(latitude)
    lng_range = distance / (111000 * math.cos(lat_rad))
    
    items = LostItem.query.filter(
        LostItem.audit_status == 'approved',
        LostItem.latitude.between(latitude - lat_range, latitude + lat_range),
        LostItem.longitude.between(longitude - lng_range, longitude + lng_range)
    ).limit(20).all()
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': [item.to_dict() for item in items]
    })
