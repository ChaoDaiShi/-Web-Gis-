from app.routes.notification import notification_bp
from app.routes.lost_item import lost_item_bp
from app.routes.claim import claim_bp
from app.routes.user import user_bp

__all__ = ['notification_bp', 'lost_item_bp', 'claim_bp', 'user_bp']