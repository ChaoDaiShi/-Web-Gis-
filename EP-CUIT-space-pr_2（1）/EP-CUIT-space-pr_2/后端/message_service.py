from flask import Blueprint, jsonify, request
import pymysql
from datetime import datetime

message_bp = Blueprint('message', __name__)

# ================== 数据库配置 ==================
DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}


def get_conn():
    return pymysql.connect(**DB_CONFIG)


# ================== 创建消息表 ==================
def create_message_table():
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                message_type ENUM('system', 'claim', 'publish', 'reminder') DEFAULT 'system',
                is_read BOOLEAN DEFAULT FALSE,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        conn.commit()
        print("消息表创建成功")
    except Exception as e:
        print(f"消息表创建失败: {e}")
    finally:
        cursor.close()
        conn.close()


# ================== 获取用户消息列表 ==================
@message_bp.route('/my/messages', methods=['GET'])
def get_user_messages():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "message": "用户ID不能为空"}), 400
    
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                message_id,
                title,
                content,
                message_type,
                is_read,
                create_time
            FROM messages 
            WHERE user_id = %s 
            ORDER BY create_time DESC
        """, (user_id,))
        
        messages = cursor.fetchall()
        
        return jsonify({
            "success": True,
            "data": messages
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ================== 标记消息为已读 ==================
@message_bp.route('/my/messages/read', methods=['POST'])
def mark_message_read():
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "参数不能为空"}), 400
    
    message_id = data.get('message_id')
    user_id = data.get('user_id')
    
    if not message_id or not user_id:
        return jsonify({"success": False, "message": "消息ID和用户ID不能为空"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE messages 
            SET is_read = TRUE 
            WHERE message_id = %s AND user_id = %s
        """, (message_id, user_id))
        
        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "消息不存在或无权操作"}), 404
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "消息已标记为已读"
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ================== 发送系统消息 ==================
@message_bp.route('/messages/send', methods=['POST'])
def send_system_message():
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "参数不能为空"}), 400
    
    user_id = data.get('user_id')
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    message_type = data.get('message_type', 'system')
    
    if not user_id or not title or not content:
        return jsonify({"success": False, "message": "用户ID、标题和内容不能为空"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO messages (user_id, title, content, message_type)
            VALUES (%s, %s, %s, %s)
        """, (user_id, title, content, message_type))
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "消息发送成功"
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ================== 获取未读消息数量 ==================
@message_bp.route('/my/messages/unread-count', methods=['GET'])
def get_unread_count():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "message": "用户ID不能为空"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT COUNT(*) as unread_count 
            FROM messages 
            WHERE user_id = %s AND is_read = FALSE
        """, (user_id,))
        
        result = cursor.fetchone()
        unread_count = result[0] if result else 0
        
        return jsonify({
            "success": True,
            "unread_count": unread_count
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ================== 删除消息 ==================
@message_bp.route('/my/messages/delete', methods=['POST'])
def delete_message():
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "参数不能为空"}), 400
    
    message_id = data.get('message_id')
    user_id = data.get('user_id')
    
    if not message_id or not user_id:
        return jsonify({"success": False, "message": "消息ID和用户ID不能为空"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM messages 
            WHERE message_id = %s AND user_id = %s
        """, (message_id, user_id))
        
        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "消息不存在或无权操作"}), 404
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "消息删除成功"
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ================== 初始化消息表 ==================
# 注意：此功能已移至 init_messages.py 中
# 如需初始化数据库，请运行: python init_messages.py

# 移除自动执行代码，避免导入时意外执行表创建操作
# 初始化功能已移至专门的初始化脚本中

# 仅在直接运行时创建表
if __name__ == "__main__":
    create_message_table()