from flask import Blueprint, jsonify, request
from . import get_conn, logger

message_send_bp = Blueprint('message_send', __name__)

@message_send_bp.route('/messages/send', methods=['POST'])
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
