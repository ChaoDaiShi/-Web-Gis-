from flask import Blueprint, jsonify, request
from . import get_conn, logger
from datetime import datetime

appointment_update_bp = Blueprint('appointment_update', __name__)

@appointment_update_bp.route('/appointments/<int:appointment_id>/approve', methods=['POST'])
def approve_appointment(appointment_id):
    logger.info(f"=== 审核通过预约: appointment_id={appointment_id} ===")
    data = request.get_json()
    
    reviewer_id = data.get('reviewer_id')
    review_note = data.get('review_note', '').strip()
    
    if not reviewer_id:
        logger.warning("审核失败: 缺少reviewer_id")
        return jsonify({"success": False, "message": "缺少审核人ID"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT a.appointment_id, a.item_id, a.user_id, a.status, l.title
            FROM appointment a
            LEFT JOIN lost_item l ON a.item_id = l.item_id
            WHERE a.appointment_id = %s
        """, (appointment_id,))
        
        appointment = cursor.fetchone()
        
        if not appointment:
            logger.warning(f"预约不存在: appointment_id={appointment_id}")
            return jsonify({"success": False, "message": "预约不存在"}), 404
        
        if appointment[3] != 'pending':
            logger.warning(f"预约状态不允许审核: status={appointment[3]}")
            return jsonify({"success": False, "message": "该预约已审核，不能重复操作"}), 400
        
        item_id = appointment[1]
        user_id = appointment[2]
        item_title = appointment[4]
        
        cursor.execute("""
            UPDATE appointment 
            SET status = 'approved', 
                reviewer_id = %s, 
                review_time = %s, 
                review_note = %s,
                update_time = %s
            WHERE appointment_id = %s
        """, (reviewer_id, datetime.now(), review_note, datetime.now(), appointment_id))
        
        cursor.execute("""
            INSERT INTO messages (user_id, title, content, message_type)
            VALUES (%s, %s, %s, 'system')
        """, (user_id, '预约审核通过', f'您的预约申请已通过审核！物品：{item_title}。请按预约时间和地点前往领取。'))
        
        conn.commit()
        logger.info(f"预约审核通过: appointment_id={appointment_id}")
        
        return jsonify({
            "success": True,
            "message": "审核通过"
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"审核预约失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@appointment_update_bp.route('/appointments/<int:appointment_id>/reject', methods=['POST'])
def reject_appointment(appointment_id):
    logger.info(f"=== 审核拒绝预约: appointment_id={appointment_id} ===")
    data = request.get_json()
    
    reviewer_id = data.get('reviewer_id')
    review_note = data.get('review_note', '').strip()
    
    if not reviewer_id:
        logger.warning("审核失败: 缺少reviewer_id")
        return jsonify({"success": False, "message": "缺少审核人ID"}), 400
    
    if not review_note:
        logger.warning("审核失败: 缺少拒绝原因")
        return jsonify({"success": False, "message": "请填写拒绝原因"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT a.appointment_id, a.item_id, a.user_id, a.status, l.title
            FROM appointment a
            LEFT JOIN lost_item l ON a.item_id = l.item_id
            WHERE a.appointment_id = %s
        """, (appointment_id,))
        
        appointment = cursor.fetchone()
        
        if not appointment:
            logger.warning(f"预约不存在: appointment_id={appointment_id}")
            return jsonify({"success": False, "message": "预约不存在"}), 404
        
        if appointment[3] != 'pending':
            logger.warning(f"预约状态不允许审核: status={appointment[3]}")
            return jsonify({"success": False, "message": "该预约已审核，不能重复操作"}), 400
        
        user_id = appointment[2]
        item_title = appointment[4]
        
        cursor.execute("""
            UPDATE appointment 
            SET status = 'rejected', 
                reviewer_id = %s, 
                review_time = %s, 
                review_note = %s,
                update_time = %s
            WHERE appointment_id = %s
        """, (reviewer_id, datetime.now(), review_note, datetime.now(), appointment_id))
        
        cursor.execute("""
            INSERT INTO messages (user_id, title, content, message_type)
            VALUES (%s, %s, %s, 'system')
        """, (user_id, '预约审核未通过', f'您的预约申请未通过审核。物品：{item_title}。原因：{review_note}'))
        
        conn.commit()
        logger.info(f"预约审核拒绝: appointment_id={appointment_id}")
        
        return jsonify({
            "success": True,
            "message": "审核拒绝"
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"审核预约失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@appointment_update_bp.route('/appointments/<int:appointment_id>/complete', methods=['POST'])
def complete_appointment(appointment_id):
    logger.info(f"=== 完成预约: appointment_id={appointment_id} ===")
    data = request.get_json()
    
    reviewer_id = data.get('reviewer_id')
    
    if not reviewer_id:
        logger.warning("完成预约失败: 缺少reviewer_id")
        return jsonify({"success": False, "message": "缺少操作人ID"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT a.appointment_id, a.item_id, a.user_id, a.status, l.title
            FROM appointment a
            LEFT JOIN lost_item l ON a.item_id = l.item_id
            WHERE a.appointment_id = %s
        """, (appointment_id,))
        
        appointment = cursor.fetchone()
        
        if not appointment:
            logger.warning(f"预约不存在: appointment_id={appointment_id}")
            return jsonify({"success": False, "message": "预约不存在"}), 404
        
        if appointment[3] != 'approved':
            logger.warning(f"预约状态不允许完成: status={appointment[3]}")
            return jsonify({"success": False, "message": "该预约未通过审核或已完成"}), 400
        
        item_id = appointment[1]
        user_id = appointment[2]
        item_title = appointment[4]
        
        cursor.execute("""
            UPDATE appointment 
            SET status = 'completed', 
                update_time = %s
            WHERE appointment_id = %s
        """, (datetime.now(), appointment_id))
        
        cursor.execute("""
            UPDATE lost_item 
            SET status = 1, 
                claimer_id = %s,
                update_time = %s
            WHERE item_id = %s
        """, (user_id, datetime.now(), item_id))
        
        cursor.execute("""
            INSERT INTO messages (user_id, title, content, message_type)
            VALUES (%s, %s, %s, 'system')
        """, (user_id, '物品领取成功', f'恭喜！您已成功领取物品：{item_title}。感谢使用校园失物招领系统！'))
        
        conn.commit()
        logger.info(f"预约完成: appointment_id={appointment_id}, item_id={item_id}")
        
        return jsonify({
            "success": True,
            "message": "领取完成"
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"完成预约失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@appointment_update_bp.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
def cancel_appointment(appointment_id):
    logger.info(f"=== 取消预约: appointment_id={appointment_id} ===")
    data = request.get_json()
    
    user_id = data.get('user_id')
    
    if not user_id:
        logger.warning("取消预约失败: 缺少user_id")
        return jsonify({"success": False, "message": "缺少用户ID"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT appointment_id, user_id, status, item_id
            FROM appointment 
            WHERE appointment_id = %s
        """, (appointment_id,))
        
        appointment = cursor.fetchone()
        
        if not appointment:
            logger.warning(f"预约不存在: appointment_id={appointment_id}")
            return jsonify({"success": False, "message": "预约不存在"}), 404
        
        if appointment[1] != int(user_id):
            logger.warning(f"无权取消预约: user_id={user_id}, appointment_user_id={appointment[1]}")
            return jsonify({"success": False, "message": "无权取消此预约"}), 403
        
        if appointment[2] not in ['pending', 'approved']:
            logger.warning(f"预约状态不允许取消: status={appointment[2]}")
            return jsonify({"success": False, "message": "该预约已完成或已取消"}), 400
        
        cursor.execute("""
            UPDATE appointment 
            SET status = 'cancelled', 
                update_time = %s
            WHERE appointment_id = %s
        """, (datetime.now(), appointment_id))
        
        conn.commit()
        logger.info(f"预约取消: appointment_id={appointment_id}")
        
        return jsonify({
            "success": True,
            "message": "预约已取消"
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"取消预约失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
