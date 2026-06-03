from flask import Blueprint, jsonify, request
from . import get_conn, logger
from datetime import datetime

appointment_create_bp = Blueprint('appointment_create', __name__)

@appointment_create_bp.route('/appointments/create', methods=['POST'])
def create_appointment():
    logger.info("=== 创建预约领取 ===")
    data = request.get_json()
    logger.debug(f"请求数据: {data}")
    
    if not data:
        logger.warning("创建预约失败: 参数为空")
        return jsonify({"success": False, "message": "参数不能为空"}), 400
    
    item_id = data.get('item_id')
    user_id = data.get('user_id')
    appointment_time = data.get('appointment_time')
    location = data.get('location', '').strip()
    longitude = data.get('longitude')
    latitude = data.get('latitude')
    contact_name = data.get('contact_name', '').strip()
    contact_phone = data.get('contact_phone', '').strip()
    note = data.get('note', '').strip()
    
    if not all([item_id, user_id, appointment_time, location, longitude, latitude, contact_name, contact_phone]):
        logger.warning(f"创建预约失败: 缺少必要参数")
        return jsonify({"success": False, "message": "请填写所有必填项"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT item_id, status FROM lost_item WHERE item_id = %s
        """, (item_id,))
        item = cursor.fetchone()
        
        if not item:
            logger.warning(f"物品不存在: item_id={item_id}")
            return jsonify({"success": False, "message": "物品不存在"}), 404
        
        if item[1] != 0:
            logger.warning(f"物品状态不允许预约: item_id={item_id}, status={item[1]}")
            return jsonify({"success": False, "message": "该物品已被认领或已关闭"}), 400
        
        cursor.execute("""
            SELECT appointment_id FROM appointment 
            WHERE item_id = %s AND user_id = %s AND status IN ('pending', 'approved')
        """, (item_id, user_id))
        
        if cursor.fetchone():
            logger.warning(f"已存在有效预约: item_id={item_id}, user_id={user_id}")
            return jsonify({"success": False, "message": "您已对该物品预约，请勿重复预约"}), 400
        
        logger.info(f"正在创建预约: item_id={item_id}, user_id={user_id}")
        cursor.execute("""
            INSERT INTO appointment 
            (item_id, user_id, appointment_time, location, longitude, latitude, 
             contact_name, contact_phone, note, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
        """, (item_id, user_id, appointment_time, location, longitude, latitude,
              contact_name, contact_phone, note))
        
        appointment_id = cursor.lastrowid
        conn.commit()
        logger.info(f"预约创建成功: appointment_id={appointment_id}")
        
        cursor.execute("""
            INSERT INTO messages (user_id, title, content, message_type)
            VALUES (%s, %s, %s, 'system')
        """, (user_id, '预约申请已提交', f'您已成功提交预约申请，预约时间：{appointment_time}，地点：{location}。请等待审核。'))
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "预约申请提交成功",
            "data": {"appointment_id": appointment_id}
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"创建预约失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
