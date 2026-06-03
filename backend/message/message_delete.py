from flask import Blueprint, jsonify, request
from datetime import datetime
import pymysql
from . import get_conn, logger

message_delete_bp = Blueprint('message_delete', __name__)

@message_delete_bp.route('/my/messages/delete', methods=['POST'])
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

@message_delete_bp.route('/my/messages/trash', methods=['GET'])
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

@message_delete_bp.route('/my/messages/restore', methods=['POST'])
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

@message_delete_bp.route('/my/messages/delete-permanently', methods=['POST'])
def delete_message_permanently():
    logger.info("=== 永久删除消息 ===")
    data = request.get_json()
    logger.debug(f"请求数据: {data}")
    
    if not data:
        logger.warning("永久删除失败: 参数为空")
        return jsonify({"success": False, "message": "参数不能为空"}), 400
    
    message_ids = data.get('message_ids')
    message_id = data.get('message_id')
    user_id = data.get('user_id')
    
    if not user_id:
        logger.warning("永久删除失败: user_id为空")
        return jsonify({"success": False, "message": "用户ID不能为空"}), 400
    
    ids_to_delete = []
    if message_ids:
        ids_to_delete = message_ids if isinstance(message_ids, list) else [message_ids]
    elif message_id:
        ids_to_delete = [message_id]
    else:
        logger.warning("永久删除失败: message_id和message_ids都为空")
        return jsonify({"success": False, "message": "消息ID不能为空"}), 400
    
    if len(ids_to_delete) == 0:
        logger.warning("永久删除失败: 没有有效的消息ID")
        return jsonify({"success": False, "message": "消息ID不能为空"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        placeholders = ', '.join(['%s'] * len(ids_to_delete))
        cursor.execute(f"""
            DELETE FROM messages 
            WHERE message_id IN ({placeholders}) AND user_id = %s AND is_deleted = TRUE
        """, (*ids_to_delete, user_id))
        
        deleted_count = cursor.rowcount
        if deleted_count == 0:
            logger.warning(f"没有消息被删除: ids={ids_to_delete}")
            return jsonify({"success": False, "message": "消息不存在或无权操作"}), 404
        
        conn.commit()
        logger.info(f"已永久删除 {deleted_count} 条消息: ids={ids_to_delete}")
        
        return jsonify({
            "success": True,
            "message": f"已永久删除 {deleted_count} 条消息"
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"永久删除失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@message_delete_bp.route('/my/messages/clear-trash', methods=['POST'])
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
