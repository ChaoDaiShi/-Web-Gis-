import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from DenluZhuChe import db, Config, User
from admin_api import LostItem, Category, Claim, ClaimForm, ReturnForm
from sqlalchemy import func

admin_new_bp = Blueprint('admin_new', __name__)

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth or not auth.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未授权'}), 401
        
        token = auth[7:]
        if token != 'admin_token':
            return jsonify({'code': 403, 'message': '需要管理员权限'}), 403
        
        return fn(*args, **kwargs)
    return wrapper

@admin_new_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    keyword = request.args.get('keyword', '')
    
    query = User.query
    
    if keyword:
        query = query.filter(
            db.or_(
                User.username.contains(keyword),
                User.phone.contains(keyword),
                User.email.contains(keyword)
            )
        )
    
    query = query.order_by(User.user_id.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    users = []
    for user in pagination.items:
        users.append({
            'id': user.user_id,
            'username': user.username,
            'phone': user.phone,
            'email': user.email,
            'created_at': user.create_time.strftime('%Y-%m-%d %H:%M:%S') if user.create_time else ''
        })
    
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

@admin_new_bp.route('/users/<user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404
    
    data = request.get_json()
    
    if 'phone' in data:
        user.phone = data['phone']
    if 'email' in data:
        user.email = data['email']
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': {
            'id': user.user_id,
            'username': user.username,
            'phone': user.phone,
            'email': user.email
        }
    })

@admin_new_bp.route('/users/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '删除成功'
    })

@admin_new_bp.route('/items', methods=['GET'])
@admin_required
def get_items():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    keyword = request.args.get('keyword', '')
    item_type = request.args.get('type', '')
    
    query = LostItem.query
    
    if keyword:
        query = query.filter(LostItem.title.contains(keyword))
    
    if item_type:
        query = query.filter(LostItem.type == int(item_type))
    
    query = query.order_by(LostItem.create_time.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    items = []
    for item in pagination.items:
        image_urls = []
        if item.image_urls:
            try:
                import json
                image_urls = json.loads(item.image_urls)
            except:
                image_urls = []
        
        items.append({
            'item_id': item.item_id,
            'title': item.title,
            'description': item.description,
            'type': item.type,
            'type_text': '拾到' if item.type == 1 else '丢失',
            'category_id': item.category_id,
            'status': item.status,
            'status_text': ['待处理', '已处理', '已关闭'][item.status] if item.status is not None else '未知',
            'image_urls': image_urls,
            'publisher_id': item.publisher_id,
            'location_id': item.location_id,
            'create_time': item.create_time.strftime('%Y-%m-%d %H:%M:%S') if item.create_time else '',
            'update_time': item.update_time.strftime('%Y-%m-%d %H:%M:%S') if item.update_time else ''
        })
    
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

@admin_new_bp.route('/items/<item_id>', methods=['PUT'])
@admin_required
def update_item(item_id):
    item = LostItem.query.get(item_id)
    
    if not item:
        return jsonify({'code': 404, 'message': '物品不存在'}), 404
    
    data = request.get_json()
    
    if 'title' in data:
        item.title = data['title']
    if 'description' in data:
        item.description = data['description']
    if 'type' in data:
        item.type = int(data['type'])
    if 'category_id' in data:
        item.category_id = int(data['category_id'])
    if 'status' in data:
        item.status = int(data['status'])
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '更新成功'
    })

@admin_new_bp.route('/items/<item_id>', methods=['DELETE'])
@admin_required
def delete_item(item_id):
    item = LostItem.query.get(item_id)
    
    if not item:
        return jsonify({'code': 404, 'message': '物品不存在'}), 404
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '删除成功'
    })

@admin_new_bp.route('/categories', methods=['GET'])
@admin_required
def get_categories():
    categories = Category.query.all()
    result = []
    for cat in categories:
        result.append({
            'category_id': cat.category_id,
            'name': cat.name
        })
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': result
    })

@admin_new_bp.route('/categories', methods=['POST'])
@admin_required
def add_category():
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'code': 400, 'message': '分类名称不能为空'}), 400
    
    new_cat = Category(name=name)
    db.session.add(new_cat)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '添加成功',
        'data': {
            'category_id': new_cat.category_id,
            'name': new_cat.name
        }
    })

@admin_new_bp.route('/categories/<category_id>', methods=['PUT'])
@admin_required
def update_category(category_id):
    cat = Category.query.get(category_id)
    
    if not cat:
        return jsonify({'code': 404, 'message': '分类不存在'}), 404
    
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'code': 400, 'message': '分类名称不能为空'}), 400
    
    cat.name = name
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '更新成功'
    })

@admin_new_bp.route('/categories/<category_id>', methods=['DELETE'])
@admin_required
def delete_category(category_id):
    cat = Category.query.get(category_id)
    
    if not cat:
        return jsonify({'code': 404, 'message': '分类不存在'}), 404
    
    db.session.delete(cat)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '删除成功'
    })

@admin_new_bp.route('/claim-forms', methods=['GET'])
@admin_required
def get_claim_forms():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', '')
    
    query = ClaimForm.query
    
    if status:
        query = query.filter(ClaimForm.status == int(status))
    
    query = query.order_by(ClaimForm.create_time.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    forms = []
    for form in pagination.items:
        forms.append({
            'claim_id': form.claim_id,
            'item_id': form.item_id,
            'username': form.username,
            'applicant_name': form.applicant_name,
            'applicant_phone': form.applicant_phone,
            'claim_reason': form.claim_reason,
            'item_description': form.item_description,
            'user_id': form.user_id,
            'status': form.status,
            'status_text': ['待审核', '已通过', '已拒绝'][form.status] if form.status is not None else '未知',
            'create_time': form.create_time.strftime('%Y-%m-%d %H:%M:%S') if form.create_time else ''
        })
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'claim_forms': forms,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })

@admin_new_bp.route('/return-forms', methods=['GET'])
@admin_required
def get_return_forms():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', '')
    
    query = ReturnForm.query
    
    if status:
        query = query.filter(ReturnForm.status == int(status))
    
    query = query.order_by(ReturnForm.create_time.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    forms = []
    for form in pagination.items:
        forms.append({
            'return_id': form.return_id,
            'item_id': form.item_id,
            'username': form.username,
            'applicant_name': form.applicant_name,
            'applicant_phone': form.applicant_phone,
            'return_reason': form.return_reason,
            'item_description': form.item_description,
            'user_id': form.user_id,
            'status': form.status,
            'status_text': ['待审核', '已通过', '已拒绝'][form.status] if form.status is not None else '未知',
            'create_time': form.create_time.strftime('%Y-%m-%d %H:%M:%S') if form.create_time else ''
        })
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'return_forms': forms,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })

@admin_new_bp.route('/statistics/overview', methods=['GET'])
@admin_required
def get_overview():
    try:
        total_users = User.query.count()
        total_items = LostItem.query.count()
        pending_claims = ClaimForm.query.filter(ClaimForm.status == 0).count()
        pending_returns = ReturnForm.query.filter(ReturnForm.status == 0).count()
        
        lost_items = LostItem.query.filter(LostItem.type == 0).count()
        found_items = LostItem.query.filter(LostItem.type == 1).count()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'total_users': total_users,
                'total_items': total_items,
                'pending_claims': pending_claims,
                'pending_returns': pending_returns,
                'lost_items': lost_items,
                'found_items': found_items
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@admin_new_bp.route('/statistics/items-by-category', methods=['GET'])
@admin_required
def get_items_by_category():
    try:
        query = db.session.query(
            Category.category_id,
            Category.name,
            func.count(LostItem.item_id).label('count')
        ).outerjoin(LostItem, Category.category_id == LostItem.category_id)\
         .group_by(Category.category_id, Category.name)
        
        result = []
        for row in query.all():
            result.append({
                'category_id': row.category_id,
                'name': row.name,
                'count': row.count
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@admin_new_bp.route('/statistics/items-by-status', methods=['GET'])
@admin_required
def get_items_by_status():
    try:
        query = db.session.query(
            LostItem.status,
            func.count(LostItem.item_id).label('count')
        ).group_by(LostItem.status)
        
        result = []
        status_map = {0: '待处理', 1: '已处理', 2: '已关闭'}
        for row in query.all():
            result.append({
                'status': row.status,
                'status_text': status_map.get(row.status, '未知'),
                'count': row.count
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
