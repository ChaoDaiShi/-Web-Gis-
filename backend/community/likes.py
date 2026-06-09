from flask import Blueprint, request, jsonify
from admin.admin_common import get_conn
import pymysql
from datetime import datetime

likes_bp = Blueprint('likes', __name__)

@likes_bp.route('/posts/<int:post_id>/like', methods=['POST'])
def toggle_like_post(post_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': '用户未登录'}), 401
        
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT like_id FROM post_likes WHERE post_id = %s AND user_id = %s",
            (post_id, user_id)
        )
        existing = cursor.fetchone()
        
        action = ''
        if existing:
            cursor.execute(
                "DELETE FROM post_likes WHERE post_id = %s AND user_id = %s",
                (post_id, user_id)
            )
            action = 'unliked'
        else:
            cursor.execute(
                "INSERT INTO post_likes (post_id, user_id, created_at) VALUES (%s, %s, %s)",
                (post_id, user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            action = 'liked'
            
            # 创建通知
            cursor.execute("SELECT user_id FROM community_posts WHERE post_id = %s", (post_id,))
            post_result = cursor.fetchone()
            if post_result:
                post_author_id = post_result[0]
                if str(post_author_id) != str(user_id):
                    cursor.execute("""
                        INSERT INTO notifications (user_id, trigger_user_id, type, content, post_id, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (post_author_id, user_id, 'like', '赞了你的帖子', post_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    conn.commit()
        
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) as count FROM post_likes WHERE post_id = %s", (post_id,))
        result = cursor.fetchone()
        likes_count = result['count'] if isinstance(result, dict) else result[0]
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'action': action, 'likes_count': likes_count})
    except Exception as e:
        print(f"点赞错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500