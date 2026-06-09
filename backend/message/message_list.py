from flask import Blueprint, jsonify, request
from datetime import datetime
import pymysql
from . import get_conn, logger

message_list_bp = Blueprint('message_list', __name__)

@message_list_bp.route('/my/messages', methods=['GET'])
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
