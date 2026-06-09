from flask import Blueprint, request, jsonify
from admin.admin_common import get_conn
import pymysql

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications', methods=['GET'])
def get_notifications():
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': '用户未登录'}), 401
        
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取所有通知，同时关联用户信息
        cursor.execute("""
            SELECT n.*, p.images as post_images, p.title as post_title,
                   trigger_u.username as trigger_username, trigger_u.avatar_url as trigger_avatar
            FROM notifications n
            LEFT JOIN community_posts p ON n.post_id = p.post_id
            LEFT JOIN user trigger_u ON n.trigger_user_id = trigger_u.user_id
            WHERE n.user_id = %s
            ORDER BY n.created_at DESC
        """, (user_id,))
        notifications = cursor.fetchall()
        
        result = []
        for n in notifications:
            n['created_at'] = n['created_at'].strftime('%Y-%m-%d %H:%M:%S') if n['created_at'] else ''
            
            # 处理帖子图片，获取第一张
            post_image = None
            if n.get('post_images'):
                try:
                    import json
                    images = json.loads(n['post_images'])
                    post_image = images[0] if images and len(images) > 0 else None
                except:
                    post_image = None
            
            # 直接使用关联查询的用户信息
            trigger_username = n.get('trigger_username')
            trigger_avatar = n.get('trigger_avatar')
            
            result.append({
                'notification_id': n['notification_id'],
                'user_id': n['user_id'],
                'type': n['type'],
                'content': n['content'],
                'post_id': n['post_id'],
                'comment_id': n['comment_id'],
                'is_read': n['is_read'],
                'created_at': n['created_at'],
                'trigger_username': trigger_username,
                'trigger_avatar': trigger_avatar,
                'post_image': post_image,
                'post_title': n.get('post_title')
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        print(f"获取通知错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@notifications_bp.route('/notifications/unread', methods=['GET'])
def get_unread_count():
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': '用户未登录'}), 401
        
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = 0",
            (user_id,)
        )
        result = cursor.fetchone()
        count = result[0] if result else 0
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        print(f"获取未读数量错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@notifications_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE notifications SET is_read = 1 WHERE notification_id = %s",
            (notification_id,)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '标记成功'})
    except Exception as e:
        print(f"标记已读错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@notifications_bp.route('/notifications/read-all', methods=['POST'])
def mark_all_notifications_read():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': '用户未登录'}), 401
        
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = %s AND is_read = 0",
            (user_id,)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '标记成功'})
    except Exception as e:
        print(f"标记全部已读错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500