from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """
    用户模型
    存储系统中的所有用户信息，包括失主和拾获者
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        """
        将用户对象转换为字典格式，便于JSON序列化
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class LostItem(db.Model):
    """
    失物模型
    存储失物信息，包括物品名称、描述、地点、类别等
    """
    __tablename__ = 'lost_items'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='lost')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    owner = db.relationship('User', backref='lost_items')

    def to_dict(self):
        """
        将失物对象转换为字典格式
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'category': self.category,
            'owner_id': self.owner_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Claim(db.Model):
    """
    认领申请模型
    存储用户对失物的认领申请记录，包含申请状态和处理时间
    """
    __tablename__ = 'claims'

    id = db.Column(db.Integer, primary_key=True)
    lost_item_id = db.Column(db.Integer, db.ForeignKey('lost_items.id'), nullable=False)
    claimer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    processed_at = db.Column(db.DateTime, nullable=True)

    lost_item = db.relationship('LostItem', backref='claims')
    claimer = db.relationship('User', backref='claims')

    def to_dict(self):
        """
        将认领申请对象转换为字典格式
        """
        return {
            'id': self.id,
            'lost_item_id': self.lost_item_id,
            'claimer_id': self.claimer_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

class Notification(db.Model):
    """
    通知模型
    存储系统发送给用户的各种通知消息
    """
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    related_item_id = db.Column(db.Integer, nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('User', backref='notifications')

    def to_dict(self):
        """
        将通知对象转换为字典格式
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'type': self.type,
            'related_item_id': self.related_item_id,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }