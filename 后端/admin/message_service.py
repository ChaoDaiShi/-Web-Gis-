from flask import Blueprint, jsonify, request
import pymysql
from datetime import datetime
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

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
                is_deleted BOOLEAN DEFAULT FALSE,
                delete_time DATETIME NULL,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE table_name = 'messages' AND column_name = 'is_deleted'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE messages ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE")
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE table_name = 'messages' AND column_name = 'delete_time'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE messages ADD COLUMN delete_time DATETIME NULL")
        
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
    logger.info("=== 获取用户消息列表 ===")
    user_id = request.args.get('user_id')
    logger.debug(f"请求参数 user_id: {user_id}")
    
    if not user_id:
        logger.warning("获取消息失败: 用户ID为空")
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
                is_deleted,
                delete_time,
                create_time
            FROM messages 
            WHERE user_id = %s AND is_deleted = FALSE
            ORDER BY create_time DESC
        """, (user_id,))
        
        messages = cursor.fetchall()
        logger.info(f"查询到 {len(messages)} 条消息")
        
        for msg in messages:
            if msg['create_time']:
                if isinstance(msg['create_time'], datetime):
                    msg['create_time'] = msg['create_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            "success": True,
            "data": messages
        })
        
    except Exception as e:
        logger.error(f"获取消息失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ================== 标记消息为已读 ==================
@message_bp.route('/my/messages/read', methods=['POST'])
def mark_message_read():
    logger.info("=== 标记消息为已读 ===")
    data = request.get_json()
    logger.debug(f"请求数据: {data}")
    
    if not data:
        logger.warning("标记已读失败: 参数为空")
        return jsonify({"success": False, "message": "参数不能为空"}), 400
    
    message_id = data.get('message_id')
    user_id = data.get('user_id')
    
    if not message_id or not user_id:
        logger.warning(f"标记已读失败: message_id={message_id}, user_id={user_id}")
        return jsonify({"success": False, "message": "消息ID和用户ID不能为空"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        logger.info(f"正在更新消息已读状态: message_id={message_id}, user_id={user_id}")
        cursor.execute("""
            UPDATE messages 
            SET is_read = TRUE 
            WHERE message_id = %s AND user_id = %s
        """, (message_id, user_id))
        
        if cursor.rowcount == 0:
            logger.warning(f"消息不存在或无权操作: message_id={message_id}")
            return jsonify({"success": False, "message": "消息不存在或无权操作"}), 404
        
        conn.commit()
        logger.info(f"消息已标记为已读: message_id={message_id}")
        
        return jsonify({
            "success": True,
            "message": "消息已标记为已读"
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"标记已读失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ================== 标记消息为未读 ==================
@message_bp.route('/my/messages/unread', methods=['POST'])
def mark_message_unread():
    logger.info("=== 标记消息为未读 ===")
    data = request.get_json()
    logger.debug(f"请求数据: {data}")
    
    if not data:
        logger.warning("标记未读失败: 参数为空")
        return jsonify({"success": False, "message": "参数不能为空"}), 400
    
    message_id = data.get('message_id')
    user_id = data.get('user_id')
    
    if not message_id or not user_id:
        logger.warning(f"标记未读失败: message_id={message_id}, user_id={user_id}")
        return jsonify({"success": False, "message": "消息ID和用户ID不能为空"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        logger.info(f"正在更新消息未读状态: message_id={message_id}, user_id={user_id}")
        cursor.execute("""
            UPDATE messages 
            SET is_read = FALSE 
            WHERE message_id = %s AND user_id = %s
        """, (message_id, user_id))
        
        if cursor.rowcount == 0:
            logger.warning(f"消息不存在或无权操作: message_id={message_id}")
            return jsonify({"success": False, "message": "消息不存在或无权操作"}), 404
        
        conn.commit()
        logger.info(f"消息已标记为未读: message_id={message_id}")
        
        return jsonify({
            "success": True,
            "message": "消息已标记为未读"
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"标记未读失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ================== 发送系统消息 ==================
@message_bp.route('/messages/send', methods=['POST'])
def send_system_message():
    logger.info("=== 发送系统消息 ===")
    data = request.get_json()
    logger.debug(f"请求数据: {data}")
    
    if not data:
        logger.warning("发送消息失败: 参数为空")
        return jsonify({"success": False, "message": "参数不能为空"}), 400
    
    user_id = data.get('user_id')
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    message_type = data.get('message_type', 'system')
    
    if not user_id or not title or not content:
        logger.warning(f"发送消息失败: user_id={user_id}, title={title}, content={content[:20] if content else None}...")
        return jsonify({"success": False, "message": "用户ID、标题和内容不能为空"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        logger.info(f"正在插入消息: user_id={user_id}, title={title}")
        cursor.execute("""
            INSERT INTO messages (user_id, title, content, message_type)
            VALUES (%s, %s, %s, %s)
        """, (user_id, title, content, message_type))
        
        conn.commit()
        logger.info(f"消息发送成功")
        
        return jsonify({
            "success": True,
            "message": "消息发送成功"
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"发送消息失败: {str(e)}", exc_info=True)
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
            WHERE user_id = %s AND is_read = FALSE AND is_deleted = FALSE
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


# ================== 标记所有消息为已读 ==================
@message_bp.route('/my/messages/read-all', methods=['POST'])
def mark_all_messages_read():
    logger.info("=== 标记所有消息为已读 ===")
    data = request.get_json()
    logger.debug(f"请求数据: {data}")
    
    if not data:
        logger.warning("标记全部已读失败: 参数为空")
        return jsonify({"success": False, "message": "参数不能为空"}), 400
    
    user_id = data.get('user_id')
    
    if not user_id:
        logger.warning("标记全部已读失败: 用户ID为空")
        return jsonify({"success": False, "message": "用户ID不能为空"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        logger.info(f"正在更新用户所有消息已读状态: user_id={user_id}")
        cursor.execute("""
            UPDATE messages 
            SET is_read = TRUE 
            WHERE user_id = %s AND is_read = FALSE AND is_deleted = FALSE
        """, (user_id,))
        
        affected_rows = cursor.rowcount
        conn.commit()
        logger.info(f"已将 {affected_rows} 条消息标记为已读: user_id={user_id}")
        
        return jsonify({
            "success": True,
            "message": f"已将 {affected_rows} 条消息标记为已读"
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"标记全部已读失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ================== 删除消息（移至回收站） ==================
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
            UPDATE messages 
            SET is_deleted = TRUE, delete_time = NOW()
            WHERE message_id = %s AND user_id = %s AND is_deleted = FALSE
        """, (message_id, user_id))
        
        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "消息不存在或无权操作"}), 404
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "消息已移至回收站"
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ================== 获取回收站消息 ==================
@message_bp.route('/my/messages/trash', methods=['GET'])
def get_trash_messages():
    logger.info("=== 获取回收站消息 ===")
    user_id = request.args.get('user_id')
    logger.debug(f"请求参数 user_id: {user_id}")
    
    if not user_id:
        logger.warning("获取回收站消息失败: 用户ID为空")
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
                delete_time,
                create_time
            FROM messages 
            WHERE user_id = %s AND is_deleted = TRUE
            ORDER BY delete_time DESC
        """, (user_id,))
        
        messages = cursor.fetchall()
        logger.info(f"查询到回收站消息 {len(messages)} 条")
        
        for msg in messages:
            if msg['create_time']:
                if isinstance(msg['create_time'], datetime):
                    msg['create_time'] = msg['create_time'].strftime('%Y-%m-%d %H:%M:%S')
            if msg['delete_time']:
                if isinstance(msg['delete_time'], datetime):
                    msg['delete_time'] = msg['delete_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            "success": True,
            "data": messages
        })
        
    except Exception as e:
        logger.error(f"获取回收站消息失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ================== 恢复消息 ==================
@message_bp.route('/my/messages/restore', methods=['POST'])
def restore_message():
    logger.info("=== 恢复消息 ===")
    data = request.get_json()
    logger.debug(f"请求数据: {data}")
    
    if not data:
        logger.warning("恢复消息失败: 参数为空")
        return jsonify({"success": False, "message": "参数不能为空"}), 400
    
    message_id = data.get('message_id')
    user_id = data.get('user_id')
    
    if not message_id or not user_id:
        logger.warning(f"恢复消息失败: message_id={message_id}, user_id={user_id}")
        return jsonify({"success": False, "message": "消息ID和用户ID不能为空"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE messages 
            SET is_deleted = FALSE, delete_time = NULL
            WHERE message_id = %s AND user_id = %s AND is_deleted = TRUE
        """, (message_id, user_id))
        
        if cursor.rowcount == 0:
            logger.warning(f"消息不存在或无法恢复: message_id={message_id}")
            return jsonify({"success": False, "message": "消息不存在或无法恢复"}), 404
        
        conn.commit()
        logger.info(f"消息已恢复: message_id={message_id}")
        
        return jsonify({
            "success": True,
            "message": "消息已恢复"
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"恢复消息失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ================== 永久删除消息 ==================
@message_bp.route('/my/messages/delete-permanently', methods=['POST'])
def delete_message_permanently():
    logger.info("=== 永久删除消息 ===")
    data = request.get_json()
    logger.debug(f"请求数据: {data}")
    
    if not data:
        logger.warning("永久删除失败: 参数为空")
        return jsonify({"success": False, "message": "参数不能为空"}), 400
    
    message_id = data.get('message_id')
    user_id = data.get('user_id')
    
    if not message_id or not user_id:
        logger.warning(f"永久删除失败: message_id={message_id}, user_id={user_id}")
        return jsonify({"success": False, "message": "消息ID和用户ID不能为空"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM messages 
            WHERE message_id = %s AND user_id = %s AND is_deleted = TRUE
        """, (message_id, user_id))
        
        if cursor.rowcount == 0:
            logger.warning(f"消息不存在或无权操作: message_id={message_id}")
            return jsonify({"success": False, "message": "消息不存在或无权操作"}), 404
        
        conn.commit()
        logger.info(f"消息已永久删除: message_id={message_id}")
        
        return jsonify({
            "success": True,
            "message": "消息已永久删除"
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"永久删除失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ================== 清空回收站 ==================
@message_bp.route('/my/messages/clear-trash', methods=['POST'])
def clear_trash():
    logger.info("=== 清空回收站 ===")
    data = request.get_json()
    logger.debug(f"请求数据: {data}")
    
    if not data:
        logger.warning("清空回收站失败: 参数为空")
        return jsonify({"success": False, "message": "参数不能为空"}), 400
    
    user_id = data.get('user_id')
    
    if not user_id:
        logger.warning("清空回收站失败: 用户ID为空")
        return jsonify({"success": False, "message": "用户ID不能为空"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM messages 
            WHERE user_id = %s AND is_deleted = TRUE AND delete_time < DATE_SUB(NOW(), INTERVAL 15 DAY)
        """, (user_id,))
        
        conn.commit()
        logger.info(f"回收站已清空超过15天的消息: user_id={user_id}")
        
        return jsonify({
            "success": True,
            "message": "已自动清理回收站中超过15天的消息"
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"清空回收站失败: {str(e)}", exc_info=True)
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