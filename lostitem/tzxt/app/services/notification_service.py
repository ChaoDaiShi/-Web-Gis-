from app.models.database import Notification, User, LostItem, Claim, db

class NotificationType:
    """
    通知类型常量类
    定义系统中所有通知类型的标识符
    """
    LOST_ITEM_PUBLISHED = 'lost_item_published'
    CLAIM_APPROVED = 'claim_approved'
    ITEM_CLAIMED = 'item_claimed'

class NotificationService:
    """
    通知服务类
    核心业务逻辑层，处理所有与通知相关的操作
    """

    @staticmethod
    def create_notification(user_id, title, content, notification_type, related_item_id=None):
        """
        创建单条通知记录

        参数:
            user_id: 接收通知的用户ID
            title: 通知标题
            content: 通知内容
            notification_type: 通知类型，用于区分不同业务场景
            related_item_id: 关联的失物ID（可选）

        返回:
            创建的通知对象
        """
        notification = Notification(
            user_id=user_id,
            title=title,
            content=content,
            type=notification_type,
            related_item_id=related_item_id
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @staticmethod
    def notify_lost_item_published(lost_item_id, owner_id):
        """
        通知1：失物发布成功
        当失主发布失物后，向所有拾获者（除失主外）发送通知

        参数:
            lost_item_id: 发布的失物ID
            owner_id: 失主ID（不会收到通知）

        返回:
            创建的通知列表
        """
        lost_item = LostItem.query.get(lost_item_id)
        if not lost_item:
            return None

        potential_finders = User.query.filter(User.id != owner_id).all()

        notifications = []
        for finder in potential_finders:
            notification = NotificationService.create_notification(
                user_id=finder.id,
                title='失物发布成功',
                content=f'有新的失物"{lost_item.title}"被发布，地点：{lost_item.location}，请帮助寻找失主。',
                notification_type=NotificationType.LOST_ITEM_PUBLISHED,
                related_item_id=lost_item_id
            )
            notifications.append(notification)

        return notifications

    @staticmethod
    def notify_claim_approved(claim_id):
        """
        通知2：认领申请通过
        当拾获者同意失主的认领申请后，向失主发送通知

        参数:
            claim_id: 认领申请ID

        返回:
            创建的通知对象
        """
        claim = Claim.query.get(claim_id)
        if not claim:
            return None

        lost_item = LostItem.query.get(claim.lost_item_id)
        owner = User.query.get(lost_item.owner_id)

        notification = NotificationService.create_notification(
            user_id=owner.id,
            title='认领申请通过',
            content=f'您发布的失物"{lost_item.title}"的认领申请已被同意。',
            notification_type=NotificationType.CLAIM_APPROVED,
            related_item_id=lost_item.id
        )

        return notification

    @staticmethod
    def notify_item_claimed(lost_item_id):
        """
        通知3：失物已成功认领
        当失物被成功认领后，同时向拾获者和失主发送通知

        参数:
            lost_item_id: 失物ID

        返回:
            创建的通知列表（包含拾获者和失主的通知）
        """
        lost_item = LostItem.query.get(lost_item_id)
        if not lost_item:
            return None

        owner = User.query.get(lost_item.owner_id)

        notifications = []

        if lost_item.status == 'claimed':
            claim = Claim.query.filter_by(
                lost_item_id=lost_item_id,
                status='approved'
            ).first()

            if claim:
                claimer = User.query.get(claim.claimer_id)

                owner_notification = NotificationService.create_notification(
                    user_id=owner.id,
                    title='失物已成功认领',
                    content=f'您发布的失物"{lost_item.title}"已被{claimer.username}成功认领。',
                    notification_type=NotificationType.ITEM_CLAIMED,
                    related_item_id=lost_item.id
                )
                notifications.append(owner_notification)

                claimer_notification = NotificationService.create_notification(
                    user_id=claimer.id,
                    title='失物已成功认领',
                    content=f'您已成功认领失物"{lost_item.title}"，请与失主联系取回。',
                    notification_type=NotificationType.ITEM_CLAIMED,
                    related_item_id=lost_item.id
                )
                notifications.append(claimer_notification)

        return notifications

    @staticmethod
    def get_user_notifications(user_id, unread_only=False):
        """
        获取用户的通知列表

        参数:
            user_id: 用户ID
            unread_only: 是否只返回未读通知

        返回:
            通知列表，按时间倒序排列
        """
        query = Notification.query.filter_by(user_id=user_id)
        if unread_only:
            query = query.filter_by(is_read=False)
        return query.order_by(Notification.created_at.desc()).all()

    @staticmethod
    def mark_as_read(notification_id):
        """
        将单条通知标记为已读

        参数:
            notification_id: 通知ID

        返回:
            是否成功标记
        """
        notification = Notification.query.get(notification_id)
        if notification:
            notification.is_read = True
            db.session.commit()
            return True
        return False

    @staticmethod
    def mark_all_as_read(user_id):
        """
        将用户的所有未读通知标记为已读

        参数:
            user_id: 用户ID

        返回:
            是否成功标记
        """
        Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()
        return True