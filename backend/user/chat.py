"""
聊天功能API
"""
from flask import Blueprint, request, jsonify
import pymysql
from datetime import datetime
from common.db_config import get_conn

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """获取会话列表"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': '用户未登录'}), 401
    
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询所有会话，按最后消息时间排序
        cursor.execute("""
            SELECT 
                cc.conversation_id,
                cc.user1_id,
                cc.user2_id,
                cc.last_message_time,
                CASE WHEN cc.user1_id = %s THEN cc.unread_count_user1 ELSE cc.unread_count_user2 END as unread_count,
                u.user_id as friend_id,
                u.username,
                u.avatar_url,
                cm.content as last_message,
                cm.message_type as last_message_type
            FROM chat_conversation cc
            JOIN user u ON u.user_id = CASE WHEN cc.user1_id = %s THEN cc.user2_id ELSE cc.user1_id END
            LEFT JOIN chat_message cm ON cm.message_id = cc.last_message_id
            WHERE cc.user1_id = %s OR cc.user2_id = %s
            ORDER BY cc.last_message_time DESC
        """, (int(user_id), int(user_id), int(user_id), int(user_id)))
        
        conversations = cursor.fetchall()
        
        result = []
        for conv in conversations:
            result.append({
                'conversation_id': conv['conversation_id'],
                'friend_id': conv['friend_id'],
                'username': conv['username'],
                'avatar': conv['avatar_url'] if conv['avatar_url'] else '/images/avatars/default.png',
                'last_message': conv['last_message'] or '',
                'last_message_type': conv['last_message_type'] or 'text',
                'last_message_time': conv['last_message_time'].strftime('%Y-%m-%d %H:%M:%S') if conv['last_message_time'] else '',
                'unread_count': conv['unread_count'] or 0
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        print(f"获取会话列表错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@chat_bp.route('/messages/<int:friend_id>', methods=['GET'])
def get_messages(friend_id):
    """获取与某人的聊天记录"""
    user_id = request.args.get('user_id')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 50))
    
    if not user_id:
        return jsonify({'success': False, 'message': '用户未登录'}), 401
    
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询聊天记录
        offset = (page - 1) * page_size
        cursor.execute("""
            SELECT message_id, sender_id, receiver_id, content, message_type, is_read, created_at
            FROM chat_message
            WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (int(user_id), friend_id, friend_id, int(user_id), page_size, offset))
        
        messages = cursor.fetchall()
        
        # 标记消息为已读
        cursor.execute("""
            UPDATE chat_message SET is_read = 1
            WHERE sender_id = %s AND receiver_id = %s AND is_read = 0
        """, (friend_id, int(user_id)))
        
        # 更新会话未读数
        cursor.execute("""
            UPDATE chat_conversation 
            SET unread_count_user1 = 0
            WHERE user1_id = %s AND user2_id = %s
        """, (int(user_id), friend_id))
        
        cursor.execute("""
            UPDATE chat_conversation 
            SET unread_count_user2 = 0
            WHERE user1_id = %s AND user2_id = %s
        """, (friend_id, int(user_id)))
        
        conn.commit()
        
        # 反转消息顺序（最早的在前）
        messages.reverse()
        
        result = []
        for msg in messages:
            result.append({
                'message_id': msg['message_id'],
                'sender_id': msg['sender_id'],
                'receiver_id': msg['receiver_id'],
                'content': msg['content'],
                'message_type': msg['message_type'],
                'is_read': bool(msg['is_read']),
                'created_at': msg['created_at'].strftime('%Y-%m-%d %H:%M:%S') if msg['created_at'] else '',
                'is_mine': msg['sender_id'] == int(user_id)
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        print(f"获取聊天记录错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@chat_bp.route('/send', methods=['POST'])
def send_message():
    """发送消息"""
    data = request.get_json()
    user_id = data.get('user_id')
    receiver_id = data.get('receiver_id')
    content = data.get('content', '').strip()
    message_type = data.get('message_type', 'text')
    
    if not user_id:
        return jsonify({'success': False, 'message': '用户未登录'}), 401
    
    if not receiver_id:
        return jsonify({'success': False, 'message': '接收者ID不能为空'}), 400
    
    if not content:
        return jsonify({'success': False, 'message': '消息内容不能为空'}), 400
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        now = datetime.now()
        
        # 插入消息
        cursor.execute("""
            INSERT INTO chat_message (sender_id, receiver_id, content, message_type, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (int(user_id), int(receiver_id), content, message_type, now))
        
        message_id = cursor.lastrowid
        
        # 更新或创建会话
        user1_id = min(int(user_id), int(receiver_id))
        user2_id = max(int(user_id), int(receiver_id))
        
        cursor.execute("""
            SELECT conversation_id FROM chat_conversation 
            WHERE user1_id = %s AND user2_id = %s
        """, (user1_id, user2_id))
        conv = cursor.fetchone()
        
        if conv:
            # 更新会话
            if user1_id == int(user_id):
                cursor.execute("""
                    UPDATE chat_conversation 
                    SET last_message_id = %s, last_message_time = %s, unread_count_user2 = unread_count_user2 + 1
                    WHERE conversation_id = %s
                """, (message_id, now, conv[0]))
            else:
                cursor.execute("""
                    UPDATE chat_conversation 
                    SET last_message_id = %s, last_message_time = %s, unread_count_user1 = unread_count_user1 + 1
                    WHERE conversation_id = %s
                """, (message_id, now, conv[0]))
        else:
            # 创建会话
            if user1_id == int(user_id):
                cursor.execute("""
                    INSERT INTO chat_conversation (user1_id, user2_id, last_message_id, last_message_time, unread_count_user2)
                    VALUES (%s, %s, %s, %s, 1)
                """, (user1_id, user2_id, message_id, now))
            else:
                cursor.execute("""
                    INSERT INTO chat_conversation (user1_id, user2_id, last_message_id, last_message_time, unread_count_user1)
                    VALUES (%s, %s, %s, %s, 1)
                """, (user1_id, user2_id, message_id, now))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '消息发送成功',
            'data': {
                'message_id': message_id,
                'sender_id': int(user_id),
                'receiver_id': int(receiver_id),
                'content': content,
                'message_type': message_type,
                'created_at': now.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        print(f"发送消息错误: {e}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@chat_bp.route('/unread', methods=['GET'])
def get_unread_count():
    """获取未读消息总数"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': '用户未登录'}), 401
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM chat_message 
            WHERE receiver_id = %s AND is_read = 0
        """, (int(user_id),))
        
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        print(f"获取未读消息数错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@chat_bp.route('/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    """删除消息（仅能删除自己发送的消息）"""
    data = request.get_json() or {}
    user_id = data.get('user_id') or request.args.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': '用户未登录'}), 401
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM chat_message 
            WHERE message_id = %s AND sender_id = %s
        """, (message_id, int(user_id)))
        
        if cursor.rowcount > 0:
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': '消息已删除'})
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '消息不存在或无权限删除'}), 404
    except Exception as e:
        print(f"删除消息错误: {e}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
