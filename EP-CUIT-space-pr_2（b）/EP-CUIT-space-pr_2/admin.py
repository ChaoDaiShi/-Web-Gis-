from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models import User, LostItem, ItemCategory, ClaimRecord, SystemLog, SystemConfig

admin_bp = Blueprint('admin', __name__)

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or user.role not in ['admin', 'super_admin']:
            return jsonify({'code': 403, 'message': '需要管理员权限'}), 403
        return fn(*args, **kwargs)
    return wrapper

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    keyword = request.args.get('keyword', '')
    role = request.args.get('role', '')
    status = request.args.get('status', '')
    
    query = User.query
    
    if keyword:
        query = query.filter(
            db.or_(
                User.username.contains(keyword),
                User.phone.contains(keyword),
                User.email.contains(keyword)
            )
        )
    
    if role:
        query = query.filter(User.role == role)
    
    if status:
        query = query.filter(User.status == status)
    
    query = query.order_by(User.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    users = [user.to_dict() for user in pagination.items]
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'users': users,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })

@admin_bp.route('/users/<user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404
    
    data = request.get_json()
    
    if 'role' in data:
        user.role = data['role']
    if 'status' in data:
        user.status = data['status']
    if 'phone' in data:
        user.phone = data['phone']
    if 'email' in data:
        user.email = data['email']
    
    db.session.commit()
    
    log = SystemLog(
        user_id=current_user_id,
        action='update_user',
        target_type='user',
        target_id=user_id,
        detail=f'更新用户信息: {user.username}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': user.to_dict()
    })

@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404
    
    if user.role == 'super_admin':
        return jsonify({'code': 403, 'message': '不能删除超级管理员'}), 403
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    log = SystemLog(
        user_id=current_user_id,
        action='delete_user',
        target_type='user',
        target_id=user_id,
        detail=f'删除用户: {username}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '删除成功'
    })

@admin_bp.route('/items/audit', methods=['GET'])
@admin_required
def get_pending_items():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    audit_status = request.args.get('audit_status', 'pending')
    
    query = LostItem.query.filter(LostItem.audit_status == audit_status)
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

@admin_bp.route('/items/<item_id>/audit', methods=['POST'])
@admin_required
def audit_item(item_id):
    current_user_id = get_jwt_identity()
    item = LostItem.query.get(item_id)
    
    if not item:
        return jsonify({'code': 404, 'message': '物品不存在'}), 404
    
    data = request.get_json()
    audit_status = data.get('audit_status')
    audit_remark = data.get('audit_remark', '')
    
    if audit_status not in ['approved', 'rejected']:
        return jsonify({'code': 400, 'message': '无效的审核状态'}), 400
    
    item.audit_status = audit_status
    item.audit_by = current_user_id
    item.audit_time = datetime.utcnow()
    item.audit_remark = audit_remark
    
    if audit_status == 'approved':
        item.status = 'pending'
    
    db.session.commit()
    
    log = SystemLog(
        user_id=current_user_id,
        action='audit_item',
        target_type='lost_item',
        target_id=item_id,
        detail=f'审核物品: {item.title}, 结果: {audit_status}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '审核成功',
        'data': item.to_dict()
    })

@admin_bp.route('/claims/audit', methods=['GET'])
@admin_required
def get_pending_claims():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', 'pending')
    
    query = ClaimRecord.query.filter(ClaimRecord.status == status)
    query = query.order_by(ClaimRecord.claim_time.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    claims = [claim.to_dict() for claim in pagination.items]
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'claims': claims,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })

@admin_bp.route('/claims/<claim_id>/audit', methods=['POST'])
@admin_required
def audit_claim(claim_id):
    current_user_id = get_jwt_identity()
    claim = ClaimRecord.query.get(claim_id)
    
    if not claim:
        return jsonify({'code': 404, 'message': '认领记录不存在'}), 404
    
    data = request.get_json()
    status = data.get('status')
    audit_remark = data.get('audit_remark', '')
    
    if status not in ['approved', 'rejected']:
        return jsonify({'code': 400, 'message': '无效的审核状态'}), 400
    
    claim.status = status
    claim.audit_by = current_user_id
    claim.audit_time = datetime.utcnow()
    claim.audit_remark = audit_remark
    
    if status == 'approved':
        item = LostItem.query.get(claim.item_id)
        if item:
            item.status = 'claimed'
            item.found_time = datetime.utcnow()
    
    db.session.commit()
    
    log = SystemLog(
        user_id=current_user_id,
        action='audit_claim',
        target_type='claim_record',
        target_id=claim_id,
        detail=f'审核认领申请, 结果: {status}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '审核成功',
        'data': claim.to_dict()
    })

@admin_bp.route('/categories', methods=['GET'])
@admin_required
def get_categories():
    categories = ItemCategory.query.order_by(ItemCategory.sort_order).all()
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': [cat.to_dict() for cat in categories]
    })

@admin_bp.route('/categories', methods=['POST'])
@admin_required
def create_category():
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'code': 400, 'message': '分类名称不能为空'}), 400
    
    existing = ItemCategory.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({'code': 400, 'message': '分类名称已存在'}), 400
    
    category = ItemCategory(
        name=data['name'],
        description=data.get('description'),
        sort_order=data.get('sort_order', 0),
        is_active=data.get('is_active', True)
    )
    
    db.session.add(category)
    db.session.commit()
    
    return jsonify({
        'code': 201,
        'message': '创建成功',
        'data': category.to_dict()
    }), 201

@admin_bp.route('/categories/<category_id>', methods=['PUT'])
@admin_required
def update_category(category_id):
    category = ItemCategory.query.get(category_id)
    
    if not category:
        return jsonify({'code': 404, 'message': '分类不存在'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        existing = ItemCategory.query.filter(
            ItemCategory.name == data['name'],
            ItemCategory.id != category_id
        ).first()
        if existing:
            return jsonify({'code': 400, 'message': '分类名称已存在'}), 400
        category.name = data['name']
    
    if 'description' in data:
        category.description = data['description']
    if 'sort_order' in data:
        category.sort_order = data['sort_order']
    if 'is_active' in data:
        category.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': category.to_dict()
    })

@admin_bp.route('/categories/<category_id>', methods=['DELETE'])
@admin_required
def delete_category(category_id):
    category = ItemCategory.query.get(category_id)
    
    if not category:
        return jsonify({'code': 404, 'message': '分类不存在'}), 404
    
    items_count = LostItem.query.filter_by(category_id=category_id).count()
    if items_count > 0:
        return jsonify({'code': 400, 'message': f'该分类下有{items_count}个物品，无法删除'}), 400
    
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '删除成功'
    })

@admin_bp.route('/statistics/overview', methods=['GET'])
@admin_required
def get_statistics_overview():
    total_users = User.query.count()
    total_items = LostItem.query.count()
    pending_items = LostItem.query.filter(LostItem.audit_status == 'pending').count()
    approved_items = LostItem.query.filter(LostItem.audit_status == 'approved').count()
    claimed_items = LostItem.query.filter(LostItem.status == 'claimed').count()
    total_claims = ClaimRecord.query.count()
    pending_claims = ClaimRecord.query.filter(ClaimRecord.status == 'pending').count()
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'total_users': total_users,
            'total_items': total_items,
            'pending_items': pending_items,
            'approved_items': approved_items,
            'claimed_items': claimed_items,
            'total_claims': total_claims,
            'pending_claims': pending_claims
        }
    })

@admin_bp.route('/statistics/items-by-category', methods=['GET'])
@admin_required
def get_items_by_category():
    result = db.session.query(
        ItemCategory.name,
        func.count(LostItem.id).label('count')
    ).outerjoin(
        LostItem, ItemCategory.id == LostItem.category_id
    ).group_by(
        ItemCategory.id
    ).all()
    
    data = [{'category': row.name, 'count': row.count} for row in result]
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': data
    })

@admin_bp.route('/statistics/items-by-status', methods=['GET'])
@admin_required
def get_items_by_status():
    result = db.session.query(
        LostItem.status,
        func.count(LostItem.id).label('count')
    ).group_by(
        LostItem.status
    ).all()
    
    status_map = {
        'pending': '待认领',
        'claimed': '已认领',
        'closed': '已关闭'
    }
    
    data = [{'status': status_map.get(row.status, row.status), 'count': row.count} for row in result]
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': data
    })

@admin_bp.route('/statistics/items-trend', methods=['GET'])
@admin_required
def get_items_trend():
    days = request.args.get('days', 7, type=int)
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    result = db.session.query(
        func.date(LostItem.publish_time).label('date'),
        func.count(LostItem.id).label('count')
    ).filter(
        LostItem.publish_time >= start_date
    ).group_by(
        func.date(LostItem.publish_time)
    ).order_by(
        func.date(LostItem.publish_time)
    ).all()
    
    data = [{'date': str(row.date), 'count': row.count} for row in result]
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': data
    })

@admin_bp.route('/statistics/user-activity', methods=['GET'])
@admin_required
def get_user_activity():
    days = request.args.get('days', 7, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    result = db.session.query(
        User.id,
        User.username,
        func.count(LostItem.id).label('item_count')
    ).join(
        LostItem, User.id == LostItem.publisher_id
    ).filter(
        LostItem.publish_time >= start_date
    ).group_by(
        User.id
    ).order_by(
        func.count(LostItem.id).desc()
    ).limit(limit).all()
    
    data = [{'user_id': row.id, 'username': row.username, 'item_count': row.item_count} for row in result]
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': data
    })

@admin_bp.route('/logs', methods=['GET'])
@admin_required
def get_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    action = request.args.get('action', '')
    user_id = request.args.get('user_id', '')
    
    query = SystemLog.query
    
    if action:
        query = query.filter(SystemLog.action == action)
    
    if user_id:
        query = query.filter(SystemLog.user_id == user_id)
    
    query = query.order_by(SystemLog.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    logs = [log.to_dict() for log in pagination.items]
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'logs': logs,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })

@admin_bp.route('/configs', methods=['GET'])
@admin_required
def get_configs():
    configs = SystemConfig.query.all()
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': [config.to_dict() for config in configs]
    })

@admin_bp.route('/configs/<config_key>', methods=['PUT'])
@admin_required
def update_config(config_key):
    config = SystemConfig.query.filter_by(config_key=config_key).first()
    
    if not config:
        return jsonify({'code': 404, 'message': '配置项不存在'}), 404
    
    data = request.get_json()
    
    if 'config_value' in data:
        config.config_value = data['config_value']
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': config.to_dict()
    })
