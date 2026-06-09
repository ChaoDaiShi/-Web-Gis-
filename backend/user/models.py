from datetime import datetime
from .config import db

class User(db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    avatar_url = db.Column(db.String(500))
    bg_image = db.Column(db.String(500))
    signature = db.Column(db.String(255))
    bio = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(50), default='student')

    def __repr__(self):
        return f"<User {self.username}>"
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'avatar_url': self.avatar_url,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None
        }


class Admin(db.Model):
    __tablename__ = 'admin'
    
    admin_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Admin {self.username}>"
