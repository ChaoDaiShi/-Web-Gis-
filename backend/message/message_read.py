from flask import Blueprint, jsonify, request
from . import get_conn, logger

message_read_bp = Blueprint('message_read', __name__)

@message_read_bp.route('/my/messages/read', methods=['POST'])
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

@message_read_bp.route('/my/messages/unread', methods=['POST'])
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

@message_read_bp.route('/my/messages/unread-count', methods=['GET'])
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

@message_read_bp.route('/my/messages/read-all', methods=['POST'])
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
