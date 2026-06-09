from flask import Blueprint, request, jsonify
from admin.admin_common import get_conn
import pymysql
from datetime import datetime

follows_bp = Blueprint('follows', __name__)

@follows_bp.route('/follow', methods=['POST'])
def follow_user():
    try:
        data = request.get_json()
        follower_id = data.get('follower_id')
        followee_id = data.get('followee_id')
        
        if not follower_id or not followee_id:
            return jsonify({'success': False, 'message': '用户ID不能为空'}), 400
        
        if follower_id == followee_id:
            return jsonify({'success': False, 'message': '不能关注自己'}), 400
        
        conn = get_conn()
        cursor = conn.cursor()
        
        # 检查是否已关注
        cursor.execute(
            "SELECT id FROM user_follow WHERE follower_id = %s AND followee_id = %s",
            (follower_id, followee_id)
        )
        existing = cursor.fetchone()
        
        if existing:
            # 已关注则取消关注
            cursor.execute(
                "DELETE FROM user_follow WHERE follower_id = %s AND followee_id = %s",
                (follower_id, followee_id)
            )
            action = 'unfollowed'
        else:
            # 未关注则添加关注
            cursor.execute(
                "INSERT INTO user_follow (follower_id, followee_id, created_at) VALUES (%s, %s, %s)",
                (follower_id, followee_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            action = 'followed'
            
            # 创建通知
            cursor.execute("SELECT username FROM user WHERE user_id = %s", (follower_id,))
            follower_result = cursor.fetchone()
            follower_name = follower_result[0] if follower_result else '某用户'
            
            cursor.execute("""
                INSERT INTO notifications (user_id, trigger_user_id, type, content, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (followee_id, follower_id, 'follow', f'{follower_name}关注了你', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'action': action})
    except Exception as e:
        print(f"关注用户错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@follows_bp.route('/check', methods=['GET'])
def check_follow():
    try:
        follower_id = request.args.get('follower_id')
        followee_id = request.args.get('followee_id')
        
        if not follower_id or not followee_id:
            return jsonify({'success': False, 'message': '用户ID不能为空'}), 400
        
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM user_follow WHERE follower_id = %s AND followee_id = %s",
            (follower_id, followee_id)
        )
        is_following = cursor.fetchone() is not None
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'is_following': is_following})
    except Exception as e:
        print(f"检查关注状态失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@follows_bp.route('/followers/<int:user_id>', methods=['GET'])
def get_followers(user_id):
    try:
        current_user_id = request.args.get('current_user_id')
        
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT u.user_id, u.username, u.avatar_url
            FROM user_follow f
            JOIN user u ON f.follower_id = u.user_id
            WHERE f.followee_id = %s
            ORDER BY f.created_at DESC
        """, (user_id,))
        followers = cursor.fetchall()
        
        # 如果有当前用户ID，检查关注状态
        if current_user_id:
            for follower in followers:
                cursor.execute("""
                    SELECT id FROM user_follow 
                    WHERE follower_id = %s AND followee_id = %s
                """, (current_user_id, follower['user_id']))
                follower['is_following'] = cursor.fetchone() is not None
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': followers})
    except Exception as e:
        print(f"获取粉丝列表失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@follows_bp.route('/following/<int:user_id>', methods=['GET'])
def get_following(user_id):
    try:
        current_user_id = request.args.get('current_user_id')
        
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT u.user_id, u.username, u.avatar_url
            FROM user_follow f
            JOIN user u ON f.followee_id = u.user_id
            WHERE f.follower_id = %s
            ORDER BY f.created_at DESC
        """, (user_id,))
        following = cursor.fetchall()
        
        # 如果有当前用户ID，检查关注状态
        if current_user_id:
            for followee in following:
                cursor.execute("""
                    SELECT id FROM user_follow 
                    WHERE follower_id = %s AND followee_id = %s
                """, (current_user_id, followee['user_id']))
                followee['is_following'] = cursor.fetchone() is not None
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': following})
    except Exception as e:
        print(f"获取关注列表失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@follows_bp.route('/counts/<int:user_id>', methods=['GET'])
def get_follow_counts(user_id):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) FROM user_follow WHERE follower_id = %s",
            (user_id,)
        )
        following_count = cursor.fetchone()[0]
        
        cursor.execute(
            "SELECT COUNT(*) FROM user_follow WHERE followee_id = %s",
            (user_id,)
        )
        follower_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'following_count': following_count,
            'follower_count': follower_count
        })
    except Exception as e:
        print(f"获取关注数量失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
