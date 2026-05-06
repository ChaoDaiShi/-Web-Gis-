import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Blueprint, request, jsonify
from DenluZhuChe import db, Config, create_app
from datetime import datetime
import json

admin_api_bp = Blueprint('admin_api', __name__)

class LostItem(db.Model):
    __tablename__ = 'lost_item'
    
    item_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.SmallInteger())
    category_id = db.Column(db.Integer)
    status = db.Column(db.SmallInteger())
    image_urls = db.Column(db.Text)
    publisher_id = db.Column(db.Integer)
    location_id = db.Column(db.Integer)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Claim(db.Model):
    __tablename__ = 'claim'
    
    claim_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, nullable=False)
    claimer_id = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.SmallInteger())
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

class Category(db.Model):
    __tablename__ = 'category'
    
    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

class Location(db.Model):
    __tablename__ = 'location'
    
    location_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    detail = db.Column(db.String(500))

@admin_api_bp.route('/lost_items', methods=['GET'])
def get_lost_items():
    items = LostItem.query.all()
    result = []
    for item in items:
        image_urls = []
        if item.image_urls:
            try:
                image_urls = json.loads(item.image_urls)
            except:
                image_urls = []
        
        result.append({
            'item_id': item.item_id,
            'title': item.title,
            'description': item.description,
            'type': '拾到' if item.type == 1 else '丢失',
            'category_id': item.category_id,
            'status': ['待认领', '已认领', '已关闭'][item.status] if item.status is not None else '未知',
            'image_urls': image_urls,
            'publisher_id': item.publisher_id,
            'location_id': item.location_id,
            'create_time': item.create_time.strftime('%Y-%m-%d %H:%M:%S') if item.create_time else '',
            'update_time': item.update_time.strftime('%Y-%m-%d %H:%M:%S') if item.update_time else ''
        })
    return jsonify(result)

@admin_api_bp.route('/lost_items', methods=['POST'])
def add_lost_item():
    data = request.get_json()
    try:
        image_urls = json.dumps(data.get('image_urls', []))
        
        new_item = LostItem(
            title=data['title'],
            description=data.get('description', ''),
            type=int(data.get('type', 0)),
            category_id=int(data.get('category_id', 0)),
            status=int(data.get('status', 0)),
            image_urls=image_urls,
            publisher_id=int(data.get('publisher_id', 0)),
            location_id=int(data.get('location_id', 0))
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'message': '添加成功', 'item_id': new_item.item_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_api_bp.route('/lost_items/<int:item_id>', methods=['PUT'])
def update_lost_item(item_id):
    item = LostItem.query.get(item_id)
    if not item:
        return jsonify({'success': False, 'message': '记录不存在'})
    
    data = request.get_json()
    try:
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
        if 'image_urls' in data:
            item.image_urls = json.dumps(data['image_urls'])
        if 'publisher_id' in data:
            item.publisher_id = int(data['publisher_id'])
        if 'location_id' in data:
            item.location_id = int(data['location_id'])
        
        db.session.commit()
        return jsonify({'success': True, 'message': '修改成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_api_bp.route('/lost_items/<int:item_id>', methods=['DELETE'])
def delete_lost_item(item_id):
    item = LostItem.query.get(item_id)
    if not item:
        return jsonify({'success': False, 'message': '记录不存在'})
    
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_api_bp.route('/claims', methods=['GET'])
def get_claims():
    claims = Claim.query.all()
    result = []
    for claim in claims:
        result.append({
            'claim_id': claim.claim_id,
            'item_id': claim.item_id,
            'claimer_id': claim.claimer_id,
            'message': claim.message,
            'status': ['待确认', '已确认', '已拒绝'][claim.status] if claim.status is not None else '未知',
            'create_time': claim.create_time.strftime('%Y-%m-%d %H:%M:%S') if claim.create_time else ''
        })
    return jsonify(result)

@admin_api_bp.route('/claims', methods=['POST'])
def add_claim():
    data = request.get_json()
    try:
        new_claim = Claim(
            item_id=int(data['item_id']),
            claimer_id=int(data['claimer_id']),
            message=data.get('message', ''),
            status=int(data.get('status', 0))
        )
        db.session.add(new_claim)
        db.session.commit()
        return jsonify({'success': True, 'message': '添加成功', 'claim_id': new_claim.claim_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_api_bp.route('/claims/<int:claim_id>', methods=['PUT'])
def update_claim(claim_id):
    claim = Claim.query.get(claim_id)
    if not claim:
        return jsonify({'success': False, 'message': '记录不存在'})
    
    data = request.get_json()
    try:
        if 'item_id' in data:
            claim.item_id = int(data['item_id'])
        if 'claimer_id' in data:
            claim.claimer_id = int(data['claimer_id'])
        if 'message' in data:
            claim.message = data['message']
        if 'status' in data:
            claim.status = int(data['status'])
        
        db.session.commit()
        return jsonify({'success': True, 'message': '修改成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_api_bp.route('/claims/<int:claim_id>', methods=['DELETE'])
def delete_claim(claim_id):
    claim = Claim.query.get(claim_id)
    if not claim:
        return jsonify({'success': False, 'message': '记录不存在'})
    
    try:
        db.session.delete(claim)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_api_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    result = []
    for category in categories:
        result.append({
            'category_id': category.category_id,
            'name': category.name
        })
    return jsonify(result)

@admin_api_bp.route('/categories', methods=['POST'])
def add_category():
    data = request.get_json()
    try:
        new_category = Category(
            name=data['name']
        )
        db.session.add(new_category)
        db.session.commit()
        return jsonify({'success': True, 'message': '添加成功', 'category_id': new_category.category_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_api_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({'success': False, 'message': '记录不存在'})
    
    data = request.get_json()
    try:
        if 'name' in data:
            category.name = data['name']
        
        db.session.commit()
        return jsonify({'success': True, 'message': '修改成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_api_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({'success': False, 'message': '记录不存在'})
    
    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_api_bp.route('/locations', methods=['GET'])
def get_locations():
    locations = Location.query.all()
    result = []
    for location in locations:
        result.append({
            'location_id': location.location_id,
            'name': location.name,
            'latitude': str(location.latitude) if location.latitude else '',
            'longitude': str(location.longitude) if location.longitude else '',
            'detail': location.detail
        })
    return jsonify(result)

@admin_api_bp.route('/locations', methods=['POST'])
def add_location():
    data = request.get_json()
    try:
        new_location = Location(
            name=data['name'],
            latitude=float(data.get('latitude', 0)),
            longitude=float(data.get('longitude', 0)),
            detail=data.get('detail', '')
        )
        db.session.add(new_location)
        db.session.commit()
        return jsonify({'success': True, 'message': '添加成功', 'location_id': new_location.location_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_api_bp.route('/locations/<int:location_id>', methods=['PUT'])
def update_location(location_id):
    location = Location.query.get(location_id)
    if not location:
        return jsonify({'success': False, 'message': '记录不存在'})
    
    data = request.get_json()
    try:
        if 'name' in data:
            location.name = data['name']
        if 'latitude' in data:
            location.latitude = float(data['latitude'])
        if 'longitude' in data:
            location.longitude = float(data['longitude'])
        if 'detail' in data:
            location.detail = data['detail']
        
        db.session.commit()
        return jsonify({'success': True, 'message': '修改成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_api_bp.route('/locations/<int:location_id>', methods=['DELETE'])
def delete_location(location_id):
    location = Location.query.get(location_id)
    if not location:
        return jsonify({'success': False, 'message': '记录不存在'})
    
    try:
        db.session.delete(location)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})