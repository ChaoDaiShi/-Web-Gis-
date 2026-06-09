"""
用户主页API - 查看他人主页
"""
from flask import Blueprint, request, jsonify
import pymysql
from datetime import datetime
from common.db_config import get_conn
from user.models import User
from user.config import db

user_profile_bp = Blueprint('user_profile', __name__)


def get_role_display(role):
    role_map = {
        'student': '学生',
        'teacher': '教师',
        'admin': '管理员',
        'staff': '教职工',
        'maintainer': '维修工'
    }
    return role_map.get(role, role) if role else '学生'


@user_profile_bp.route('/user/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    """获取用户主页信息"""
    current_user_id = request.args.get('current_user_id')
    
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取用户基本信息
        cursor.execute("""
            SELECT user_id, username, email, avatar_url, bg_image, signature, bio, 
                   create_time, role, phone
            FROM user WHERE user_id = %s
        """, (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 获取用户统计信息
        cursor.execute("""
            SELECT COUNT(*) as post_count FROM community_posts WHERE user_id = %s
        """, (user_id,))
        post_count = cursor.fetchone()['post_count']
        
        cursor.execute("""
            SELECT COUNT(*) as publish_count FROM lost_item WHERE publisher_id = %s
        """, (user_id,))
        publish_count = cursor.fetchone()['publish_count']
        
        cursor.execute("""
            SELECT COUNT(*) as friend_count 
            FROM user_friend WHERE user_id = %s AND status = 'accepted'
        """, (user_id,))
        friend_count = cursor.fetchone()['friend_count']
        
        # 检查好友关系
        is_friend = False
        friend_status = None
        if current_user_id:
            cursor.execute("""
                SELECT status FROM user_friend 
                WHERE user_id = %s AND friend_id = %s
            """, (int(current_user_id), user_id))
            relation = cursor.fetchone()
            if relation:
                is_friend = relation['status'] == 'accepted'
                friend_status = relation['status']
        
        # 检查是否关注
        is_following = False
        if current_user_id:
            cursor.execute("""
                SELECT 1 FROM user_follow 
                WHERE follower_id = %s AND followee_id = %s
            """, (int(current_user_id), user_id))
            is_following = cursor.fetchone() is not None
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'user_id': user['user_id'],
                'username': user['username'],
                'avatar': user['avatar_url'] if user['avatar_url'] else '/images/avatars/default.png',
                'bg_image': user['bg_image'] if user['bg_image'] else '',
                'signature': user['signature'] or '',
                'bio': user['bio'] or '',
                'create_time': user['create_time'].strftime('%Y-%m-%d') if user['create_time'] else '',
                'identity': get_role_display(user['role']),
                'role': user['role'] or '',
                'post_count': post_count,
                'publish_count': publish_count,
                'friend_count': friend_count,
                'is_friend': is_friend,
                'friend_status': friend_status,
                'is_following': is_following,
                'is_own': str(current_user_id) == str(user_id)
            }
        })
    except Exception as e:
        print(f"获取用户主页错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@user_profile_bp.route('/user/<int:user_id>/posts', methods=['GET'])
def get_user_posts(user_id):
    """获取用户发布的帖子"""
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    current_user_id = request.args.get('current_user_id')
    
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        offset = (page - 1) * page_size
        cursor.execute("""
            SELECT p.*, u.username as author_name, u.avatar_url
            FROM community_posts p
            LEFT JOIN user u ON p.user_id = u.user_id
            WHERE p.user_id = %s
            ORDER BY p.created_at DESC
            LIMIT %s OFFSET %s
        """, (user_id, page_size, offset))
        posts = cursor.fetchall()
        
        import json
        for post in posts:
            if post.get('images'):
                try:
                    post['images'] = json.loads(post['images'])
                except:
                    post['images'] = []
            else:
                post['images'] = []
            
            cursor.execute("SELECT COUNT(*) as count FROM post_likes WHERE post_id = %s", (post['post_id'],))
            post['likes_count'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM community_comments WHERE post_id = %s", (post['post_id'],))
            post['comments_count'] = cursor.fetchone()['count']
            
            post['is_liked'] = False
            if current_user_id:
                cursor.execute(
                    "SELECT 1 FROM post_likes WHERE post_id = %s AND user_id = %s",
                    (post['post_id'], current_user_id)
                )
                post['is_liked'] = cursor.fetchone() is not None
            
            post['created_at'] = post['created_at'].strftime('%Y-%m-%d %H:%M:%S') if post['created_at'] else ''
            post['author_avatar'] = post['avatar_url'] if post['avatar_url'] else ''
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': posts})
    except Exception as e:
        print(f"获取用户帖子错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@user_profile_bp.route('/user/<int:user_id>/items', methods=['GET'])
def get_user_items(user_id):
    """获取用户发布的失物"""
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        offset = (page - 1) * page_size
        cursor.execute("""
            SELECT li.item_id, li.title, li.description, li.create_time, li.status, 
                   li.type, li.image_urls, li.audit_status, l.longitude, l.latitude
            FROM lost_item li
            LEFT JOIN location l ON li.location_id = l.location_id
            WHERE li.publisher_id = %s
            ORDER BY li.create_time DESC
            LIMIT %s OFFSET %s
        """, (user_id, page_size, offset))
        items = cursor.fetchall()
        
        result = []
        for item in items:
            result.append({
                "item_id": item['item_id'],
                "title": item['title'],
                "description": item['description'] or '',
                "create_time": str(item['create_time']) if item['create_time'] else '',
                "status": item['status'],
                "type": item['type'] or 0,
                "image_urls": item['image_urls'] or '',
                "audit_status": item.get('audit_status') or 'pending',
                "lat": item['latitude'],
                "lng": item['longitude']
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        print(f"获取用户失物错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
