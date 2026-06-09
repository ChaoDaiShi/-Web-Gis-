"""
好友管理API
"""
from flask import Blueprint, request, jsonify
import pymysql
from datetime import datetime
from common.db_config import get_conn

friend_bp = Blueprint('friend', __name__)


@friend_bp.route('/friends', methods=['GET'])
def get_friends():
    """获取好友列表"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': '用户未登录'}), 401
    
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询已接受的好友关系
        cursor.execute("""
            SELECT uf.friendship_id, uf.friend_id, u.username, u.avatar_url, 
                   uf.created_at as friend_since
            FROM user_friend uf
            JOIN user u ON uf.friend_id = u.user_id
            WHERE uf.user_id = %s AND uf.status = 'accepted'
            ORDER BY uf.updated_at DESC
        """, (int(user_id),))
        friends = cursor.fetchall()
        
        result = []
        for friend in friends:
            result.append({
                'friendship_id': friend['friendship_id'],
                'friend_id': friend['friend_id'],
                'username': friend['username'],
                'avatar': friend['avatar_url'] if friend['avatar_url'] else '/images/avatars/default.png',
                'friend_since': friend['friend_since'].strftime('%Y-%m-%d %H:%M:%S') if friend['friend_since'] else ''
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        print(f"获取好友列表错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@friend_bp.route('/friends/requests', methods=['GET'])
def get_friend_requests():
    """获取好友请求列表"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': '用户未登录'}), 401
    
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询收到的好友请求
        cursor.execute("""
            SELECT uf.friendship_id, uf.user_id as requester_id, u.username, u.avatar_url,
                   uf.created_at
            FROM user_friend uf
            JOIN user u ON uf.user_id = u.user_id
            WHERE uf.friend_id = %s AND uf.status = 'pending'
            ORDER BY uf.created_at DESC
        """, (int(user_id),))
        requests = cursor.fetchall()
        
        result = []
        for req in requests:
            result.append({
                'friendship_id': req['friendship_id'],
                'requester_id': req['requester_id'],
                'username': req['username'],
                'avatar': req['avatar_url'] if req['avatar_url'] else '/images/avatars/default.png',
                'created_at': req['created_at'].strftime('%Y-%m-%d %H:%M:%S') if req['created_at'] else ''
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        print(f"获取好友请求错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@friend_bp.route('/friends/request', methods=['POST'])
def send_friend_request():
    """发送好友请求"""
    data = request.get_json()
    user_id = data.get('user_id')
    friend_id = data.get('friend_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': '用户未登录'}), 401
    
    if not friend_id:
        return jsonify({'success': False, 'message': '好友ID不能为空'}), 400
    
    if user_id == friend_id:
        return jsonify({'success': False, 'message': '不能添加自己为好友'}), 400
    
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 检查是否已存在好友关系
        cursor.execute("""
            SELECT friendship_id, status FROM user_friend 
            WHERE user_id = %s AND friend_id = %s
        """, (int(user_id), int(friend_id)))
        existing = cursor.fetchone()
        
        if existing:
            if existing['status'] == 'accepted':
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': '已经是好友了'}), 400
            elif existing['status'] == 'pending':
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': '已发送过好友请求'}), 400
            elif existing['status'] == 'rejected':
                # 重新发送请求
                cursor.execute("""
                    UPDATE user_friend SET status = 'pending', updated_at = %s
                    WHERE friendship_id = %s
                """, (datetime.now(), existing['friendship_id']))
                conn.commit()
                cursor.close()
                conn.close()
                return jsonify({'success': True, 'message': '好友请求已发送'})
        
        # 检查对方是否已发送请求
        cursor.execute("""
            SELECT friendship_id FROM user_friend 
            WHERE user_id = %s AND friend_id = %s AND status = 'pending'
        """, (int(friend_id), int(user_id)))
        reverse_pending = cursor.fetchone()
        
        if reverse_pending:
            # 对方已发送请求，直接接受
            cursor.execute("""
                UPDATE user_friend SET status = 'accepted', updated_at = %s
                WHERE friendship_id = %s
            """, (datetime.now(), reverse_pending['friendship_id']))
            
            # 创建双向关系
            cursor.execute("""
                INSERT INTO user_friend (user_id, friend_id, status, created_at, updated_at)
                VALUES (%s, %s, 'accepted', %s, %s)
            """, (int(user_id), int(friend_id), datetime.now(), datetime.now()))
            
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': '已自动接受对方的好友请求，你们现在是好友了'})
        
        # 创建新的好友请求
        cursor.execute("""
            INSERT INTO user_friend (user_id, friend_id, status, created_at, updated_at)
            VALUES (%s, %s, 'pending', %s, %s)
        """, (int(user_id), int(friend_id), datetime.now(), datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '好友请求已发送'})
    except Exception as e:
        print(f"发送好友请求错误: {e}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@friend_bp.route('/friends/accept/<int:friendship_id>', methods=['POST'])
def accept_friend_request(friendship_id):
    """接受好友请求"""
    data = request.get_json() or {}
    user_id = data.get('user_id') or request.args.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': '用户未登录'}), 401
    
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 验证请求是否属于当前用户
        cursor.execute("""
            SELECT user_id, friend_id FROM user_friend 
            WHERE friendship_id = %s AND friend_id = %s AND status = 'pending'
        """, (friendship_id, int(user_id)))
        request_record = cursor.fetchone()
        
        if not request_record:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '好友请求不存在或已处理'}), 404
        
        requester_id = request_record['user_id']
        
        # 更新请求状态
        cursor.execute("""
            UPDATE user_friend SET status = 'accepted', updated_at = %s
            WHERE friendship_id = %s
        """, (datetime.now(), friendship_id))
        
        # 创建双向好友关系
        cursor.execute("""
            INSERT INTO user_friend (user_id, friend_id, status, created_at, updated_at)
            VALUES (%s, %s, 'accepted', %s, %s)
            ON DUPLICATE KEY UPDATE status = 'accepted', updated_at = %s
        """, (int(user_id), requester_id, datetime.now(), datetime.now(), datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '已接受好友请求'})
    except Exception as e:
        print(f"接受好友请求错误: {e}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@friend_bp.route('/friends/reject/<int:friendship_id>', methods=['POST'])
def reject_friend_request(friendship_id):
    """拒绝好友请求"""
    data = request.get_json() or {}
    user_id = data.get('user_id') or request.args.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': '用户未登录'}), 401
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE user_friend SET status = 'rejected', updated_at = %s
            WHERE friendship_id = %s AND friend_id = %s AND status = 'pending'
        """, (datetime.now(), friendship_id, int(user_id)))
        
        if cursor.rowcount > 0:
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': '已拒绝好友请求'})
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '好友请求不存在或已处理'}), 404
    except Exception as e:
        print(f"拒绝好友请求错误: {e}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@friend_bp.route('/friends/<int:friend_id>', methods=['DELETE'])
def delete_friend(friend_id):
    """删除好友"""
    data = request.get_json() or {}
    user_id = data.get('user_id') or request.args.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': '用户未登录'}), 401
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # 删除双向关系
        cursor.execute("""
            DELETE FROM user_friend 
            WHERE (user_id = %s AND friend_id = %s) 
               OR (user_id = %s AND friend_id = %s)
        """, (int(user_id), friend_id, friend_id, int(user_id)))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '已删除好友'})
    except Exception as e:
        print(f"删除好友错误: {e}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@friend_bp.route('/friends/check', methods=['GET'])
def check_friendship():
    """检查好友关系"""
    user_id = request.args.get('user_id')
    friend_id = request.args.get('friend_id')
    
    if not user_id or not friend_id:
        return jsonify({'success': False, 'message': '参数不完整'}), 400
    
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT status FROM user_friend 
            WHERE user_id = %s AND friend_id = %s
        """, (int(user_id), int(friend_id)))
        relation = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if relation:
            return jsonify({
                'success': True,
                'is_friend': relation['status'] == 'accepted',
                'status': relation['status']
            })
        else:
            return jsonify({
                'success': True,
                'is_friend': False,
                'status': None
            })
    except Exception as e:
        print(f"检查好友关系错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


def add_friend_auto(user_id, friend_id):
    """自动添加好友（用于失主和拾到者自动加好友）"""
    if user_id == friend_id:
        return False
    
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 检查是否已是好友
        cursor.execute("""
            SELECT friendship_id, status FROM user_friend 
            WHERE user_id = %s AND friend_id = %s
        """, (int(user_id), int(friend_id)))
        existing = cursor.fetchone()
        
        if existing and existing['status'] == 'accepted':
            cursor.close()
            conn.close()
            return True
        
        # 创建或更新双向好友关系
        now = datetime.now()
        
        if existing:
            cursor.execute("""
                UPDATE user_friend SET status = 'accepted', updated_at = %s
                WHERE friendship_id = %s
            """, (now, existing['friendship_id']))
        else:
            cursor.execute("""
                INSERT INTO user_friend (user_id, friend_id, status, created_at, updated_at)
                VALUES (%s, %s, 'accepted', %s, %s)
            """, (int(user_id), int(friend_id), now, now))
        
        # 创建反向关系
        cursor.execute("""
            INSERT INTO user_friend (user_id, friend_id, status, created_at, updated_at)
            VALUES (%s, %s, 'accepted', %s, %s)
            ON DUPLICATE KEY UPDATE status = 'accepted', updated_at = %s
        """, (int(friend_id), int(user_id), now, now, now))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"自动添加好友错误: {e}")
        if conn:
            conn.rollback()
        return False
