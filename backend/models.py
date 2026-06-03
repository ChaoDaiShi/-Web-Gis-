from datetime import datetime
from user.config import db

class ItemCategory(db.Model):
    __tablename__ = 'category'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_active': self.is_active
        }

class LostItem(db.Model):
    __tablename__ = 'lost_item'

    item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.SmallInteger, nullable=False)
    category_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.SmallInteger, default=0)
    image_urls = db.Column(db.JSON)
    publisher_id = db.Column(db.Integer, nullable=False)
    location_id = db.Column(db.Integer)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    audit_status = db.Column(db.String(20), default='pending')
    audit_time = db.Column(db.DateTime)
    audit_remark = db.Column(db.String(200))
    audit_by = db.Column(db.Integer)

    def to_dict(self):
        return {
            'item_id': self.item_id,
            'id': self.item_id,
            'title': self.title,
            'description': self.description,
            'category_id': self.category_id,
            'category_name': None,
            'item_type': 'lost' if self.type == 0 else 'found',
            'status': 'pending' if self.status == 0 else 'claimed' if self.status == 1 else 'closed',
            'image_url': self.image_urls,
            'publisher_id': self.publisher_id,
            'publisher_name': None,
            'publish_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'audit_status': self.audit_status or 'pending',
            'view_count': 0
        }

class ClaimRecord(db.Model):
    __tablename__ = 'claim'
    
    claim_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.Integer, nullable=False)
    claimer_id = db.Column(db.Integer, nullable=False)
    claim_time = db.Column(db.DateTime, default=datetime.utcnow)
    claim_reason = db.Column(db.Text)
    proof_info = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')
    audit_by = db.Column(db.Integer)
    audit_time = db.Column(db.DateTime)
    audit_remark = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.claim_id,
            'item_id': self.item_id,
            'item_title': None,
            'claimer_id': self.claimer_id,
            'claimer_name': None,
            'claim_time': self.claim_time.strftime('%Y-%m-%d %H:%M:%S') if self.claim_time else None,
            'claim_reason': self.claim_reason,
            'proof_info': self.proof_info,
            'status': self.status,
            'audit_remark': self.audit_remark
        }

class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    action = db.Column(db.String(50), nullable=False)
    target_type = db.Column(db.String(50))
    target_id = db.Column(db.String(20))
    detail = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'detail': self.detail,
            'ip_address': self.ip_address,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
