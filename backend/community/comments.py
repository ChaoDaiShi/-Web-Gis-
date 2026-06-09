from flask import Blueprint, request, jsonify
from admin.admin_common import get_conn
import pymysql
from datetime import datetime

comments_bp = Blueprint('comments', __name__)

@comments_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    try:
        viewer_id = request.args.get('user_id')
        
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT c.*, u.username as author_name, u.avatar_url
            FROM community_comments c
            LEFT JOIN user u ON c.user_id = u.user_id
            WHERE c.post_id = %s
            ORDER BY c.created_at ASC
        """, (post_id,))
        comments = cursor.fetchall()
        
        for comment in comments:
            comment['created_at'] = comment['created_at'].strftime('%Y-%m-%d %H:%M:%S') if comment['created_at'] else ''
            comment['author_avatar'] = comment['avatar_url'] if comment['avatar_url'] else ''
            
            cursor.execute("SELECT COUNT(*) as count FROM comment_likes WHERE comment_id = %s", (comment['comment_id'],))
            likes_result = cursor.fetchone()
            comment['likes_count'] = likes_result['count'] if likes_result else 0
            
            if viewer_id:
                cursor.execute("""
                    SELECT 1 FROM comment_likes 
                    WHERE comment_id = %s AND user_id = %s
                """, (comment['comment_id'], viewer_id))
                comment['is_liked'] = cursor.fetchone() is not None
            else:
                comment['is_liked'] = False
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': comments})
    except Exception as e:
        print(f"获取评论错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@comments_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
def create_comment(post_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': '用户未登录'}), 401
        
        if not content:
            return jsonify({'success': False, 'message': '评论内容不能为空'}), 400
        
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO community_comments (post_id, user_id, parent_id, content, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (post_id, user_id, parent_id, content, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        comment_id = cursor.lastrowid
        
        # 创建通知
        cursor.execute("SELECT user_id FROM community_posts WHERE post_id = %s", (post_id,))
        post_result = cursor.fetchone()
        if post_result:
            post_author_id = post_result[0]
            if str(post_author_id) != str(user_id):
                cursor.execute("""
                    INSERT INTO notifications (user_id, trigger_user_id, type, content, post_id, comment_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (post_author_id, user_id, 'comment', content[:100], post_id, comment_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '评论成功', 'comment_id': comment_id})
    except Exception as e:
        print(f"发表评论错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@comments_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': '用户未登录'}), 401
        
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id, post_id FROM community_comments WHERE comment_id = %s", (comment_id,))
        comment = cursor.fetchone()
        
        if not comment:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '评论不存在'}), 404
        
        cursor.execute("SELECT user_id FROM community_posts WHERE post_id = %s", (comment[1],))
        post = cursor.fetchone()
        
        if str(comment[0]) != str(user_id) and (not post or str(post[0]) != str(user_id)):
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '无权限删除'}), 403
        
        cursor.execute("DELETE FROM comment_likes WHERE comment_id = %s", (comment_id,))
        
        cursor.execute("DELETE FROM community_comments WHERE parent_id = %s", (comment_id,))
        
        cursor.execute("DELETE FROM community_comments WHERE comment_id = %s", (comment_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        print(f"删除评论错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@comments_bp.route('/comments/<int:comment_id>/like', methods=['POST'])
def toggle_like_comment(comment_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': '用户未登录'}), 401
        
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT like_id FROM comment_likes WHERE comment_id = %s AND user_id = %s", 
                       (comment_id, user_id))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("DELETE FROM comment_likes WHERE comment_id = %s AND user_id = %s",
                          (comment_id, user_id))
            action = 'unliked'
        else:
            cursor.execute("INSERT INTO comment_likes (comment_id, user_id, created_at) VALUES (%s, %s, %s)",
                          (comment_id, user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            action = 'liked'
        
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) as count FROM comment_likes WHERE comment_id = %s", (comment_id,))
        result = cursor.fetchone()
        likes_count = result[0] if result else 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'action': action, 
            'likes_count': likes_count
        })
    except Exception as e:
        print(f"评论点赞错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500