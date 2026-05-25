from flask import Blueprint, request, jsonify
from app.models.database import Claim, LostItem, User, db
from app.services.notification_service import NotificationService
from datetime import datetime

claim_bp = Blueprint('claims', __name__)

@claim_bp.route('/', methods=['POST'])
def create_claim():
    """
    创建新的认领申请

    请求体 (JSON):
        lost_item_id: 失物ID（必需）
        claimer_id: 认领者用户ID（必需）

    返回:
        成功消息和创建的认领申请信息
    """
    data = request.get_json()

    if not data or not data.get('lost_item_id') or not data.get('claimer_id'):
        return jsonify({'error': 'Missing required fields'}), 400

    lost_item = LostItem.query.get(data['lost_item_id'])
    if not lost_item:
        return jsonify({'error': 'Lost item not found'}), 404

    claimer = User.query.get(data['claimer_id'])
    if not claimer:
        return jsonify({'error': 'Claimer not found'}), 404

    existing_claim = Claim.query.filter_by(
        lost_item_id=data['lost_item_id'],
        claimer_id=data['claimer_id'],
        status='pending'
    ).first()

    if existing_claim:
        return jsonify({'error': 'Claim already exists'}), 400

    claim = Claim(
        lost_item_id=data['lost_item_id'],
        claimer_id=data['claimer_id'],
        status='pending'
    )

    db.session.add(claim)
    db.session.commit()

    return jsonify({
        'message': 'Claim created successfully',
        'claim': claim.to_dict()
    }), 201

@claim_bp.route('/<int:claim_id>/approve', methods=['PUT'])
def approve_claim(claim_id):
    """
    同意认领申请

    当拾获者同意失主的认领申请时：
    1. 更新认领申请状态为 'approved'
    2. 更新失物状态为 'claimed'
    3. 向失主发送"认领申请通过"通知
    4. 向拾获者和失主发送"失物已成功认领"通知

    路径参数:
        claim_id: 认领申请ID

    返回:
        成功消息和更新后的认领申请信息
    """
    claim = Claim.query.get(claim_id)
    if not claim:
        return jsonify({'error': 'Claim not found'}), 404

    if claim.status != 'pending':
        return jsonify({'error': 'Claim is not pending'}), 400

    claim.status = 'approved'
    claim.processed_at = datetime.utcnow()

    lost_item = LostItem.query.get(claim.lost_item_id)
    lost_item.status = 'claimed'

    db.session.commit()

    NotificationService.notify_claim_approved(claim_id)

    NotificationService.notify_item_claimed(lost_item.id)

    return jsonify({
        'message': 'Claim approved successfully',
        'claim': claim.to_dict()
    })

@claim_bp.route('/<int:claim_id>/reject', methods=['PUT'])
def reject_claim(claim_id):
    """
    拒绝认领申请

    路径参数:
        claim_id: 认领申请ID

    返回:
        成功消息和更新后的认领申请信息
    """
    claim = Claim.query.get(claim_id)
    if not claim:
        return jsonify({'error': 'Claim not found'}), 404

    if claim.status != 'pending':
        return jsonify({'error': 'Claim is not pending'}), 400

    claim.status = 'rejected'
    claim.processed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        'message': 'Claim rejected successfully',
        'claim': claim.to_dict()
    })

@claim_bp.route('/lost-item/<int:lost_item_id>', methods=['GET'])
def get_claims_by_lost_item(lost_item_id):
    """
    获取某个失物的所有认领申请

    路径参数:
        lost_item_id: 失物ID

    返回:
        认领申请列表和总数
    """
    claims = Claim.query.filter_by(lost_item_id=lost_item_id).order_by(Claim.created_at.desc()).all()
    return jsonify({
        'claims': [c.to_dict() for c in claims],
        'total': len(claims)
    })

@claim_bp.route('/user/<int:user_id>', methods=['GET'])
def get_claims_by_user(user_id):
    """
    获取某个用户提交的所有认领申请

    路径参数:
        user_id: 用户ID

    返回:
        认领申请列表和总数
    """
    claims = Claim.query.filter_by(claimer_id=user_id).order_by(Claim.created_at.desc()).all()
    return jsonify({
        'claims': [c.to_dict() for c in claims],
        'total': len(claims)
    })