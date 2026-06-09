"""拾到者预约归还API - 获取可预约归还的失主列表"""
from flask import Blueprint, jsonify, request
from . import get_conn, logger

return_appointment_bp = Blueprint('return_appointment', __name__)

@return_appointment_bp.route('/return-appointments/available-owners', methods=['GET'])
def get_available_owners():
    """
    获取拾到者可以预约归还的失主列表
    条件：拾到者发布的物品被认领且审核通过
    """
    logger.info("=== 获取可预约归还的失主列表 ===")
    
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '缺少用户ID'}), 400
    
    logger.info(f"查询用户ID: {user_id}")
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        # 先查询用户发布的所有物品
        cursor.execute("""
            SELECT item_id, title, status FROM lost_item WHERE publisher_id = %s
        """, (user_id,))
        all_items = cursor.fetchall()
        logger.info(f"用户发布的物品: {all_items}")
        
        # 查询拾到者发布的物品，且已被认领通过
        # lost_item.status = 1 表示已被认领
        # claim_form.status = 1 表示认领审核通过
        cursor.execute("""
            SELECT 
                li.item_id,
                li.title,
                li.description,
                li.image_urls,
                cf.claim_id,
                cf.user_id as owner_id,
                u.username as owner_name,
                u.avatar_url as owner_avatar,
                u.phone as owner_phone,
                cf.create_time as claim_time
            FROM lost_item li
            INNER JOIN claim_form cf ON li.item_id = cf.item_id AND cf.status = 1
            INNER JOIN user u ON cf.user_id = u.user_id
            WHERE li.publisher_id = %s AND li.status = 1
            ORDER BY cf.create_time DESC
        """, (user_id,))
        
        items = cursor.fetchall()
        logger.info(f"查询到的可预约归还物品数量: {len(items)}")
        
        result = []
        for item in items:
            # 检查是否已有待处理的预约
            cursor.execute("""
                SELECT appointment_id, status 
                FROM appointment 
                WHERE item_id = %s AND user_id = %s AND status IN ('pending', 'approved')
            """, (item[0], user_id))
            existing = cursor.fetchone()
            
            result.append({
                'item_id': item[0],
                'item_title': item[1],
                'item_description': item[2],
                'item_images': item[3],
                'claim_id': item[4],
                'owner_id': item[5],
                'owner_name': item[6],
                'owner_avatar': item[7],
                'owner_phone': item[8],
                'claim_time': item[9].strftime('%Y-%m-%d %H:%M:%S') if item[9] else None,
                'has_pending_appointment': existing is not None,
                'appointment_status': existing[1] if existing else None
            })
        
        logger.info(f"找到 {len(result)} 条可预约归还记录")
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        logger.error(f"获取可预约归还列表失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@return_appointment_bp.route('/return-appointments/create', methods=['POST'])
def create_return_appointment():
    """
    创建预约归还申请
    发送给失主的消息通知
    """
    logger.info("=== 创建预约归还申请 ===")
    data = request.get_json()
    logger.debug(f"请求数据: {data}")
    
    if not data:
        return jsonify({'success': False, 'message': '参数不能为空'}), 400
    
    item_id = data.get('item_id')
    finder_id = data.get('finder_id')  # 拾到者ID
    owner_id = data.get('owner_id')    # 失主ID
    appointment_date = data.get('appointment_date')  # 归还日期
    appointment_time = data.get('appointment_time')  # 归还时间（时:分）
    location = data.get('location', '').strip()
    longitude = data.get('longitude')
    latitude = data.get('latitude')
    note = data.get('note', '').strip()
    
    if not all([item_id, finder_id, owner_id, appointment_date, appointment_time, location, longitude, latitude]):
        return jsonify({'success': False, 'message': '请填写所有必填项'}), 400
    
    # 组合完整的预约时间
    appointment_datetime = f"{appointment_date} {appointment_time}"
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        # 检查是否已有待处理的预约
        cursor.execute("""
            SELECT appointment_id FROM appointment 
            WHERE item_id = %s AND user_id = %s AND status IN ('pending', 'approved')
        """, (item_id, finder_id))
        
        if cursor.fetchone():
            return jsonify({'success': False, 'message': '已存在待处理的预约'}), 400
        
        # 创建预约记录
        cursor.execute("""
            INSERT INTO appointment 
            (item_id, user_id, appointment_time, location, longitude, latitude, 
             contact_name, contact_phone, note, status, target_user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s)
        """, (item_id, finder_id, appointment_datetime, location, longitude, latitude,
              '', '', note, owner_id))
        
        appointment_id = cursor.lastrowid
        
        # 获取物品信息
        cursor.execute("SELECT title FROM lost_item WHERE item_id = %s", (item_id,))
        item = cursor.fetchone()
        item_title = item[0] if item else '未知物品'
        
        # 获取拾到者信息
        cursor.execute("SELECT username FROM user WHERE user_id = %s", (finder_id,))
        finder = cursor.fetchone()
        finder_name = finder[0] if finder else '拾到者'
        
        # 发送消息通知给失主
        cursor.execute("""
            INSERT INTO messages (user_id, title, content, message_type, related_id, related_type)
            VALUES (%s, %s, %s, 'appointment', %s, 'appointment')
        """, (owner_id, 
              f'预约归还通知 - {item_title}',
              f'{finder_name} 想要预约归还您丢失的物品「{item_title}」\n预约时间：{appointment_datetime}\n预约地点：{location}\n\n请前往"我的预约"查看详情并确认。',
              appointment_id))
        
        conn.commit()
        logger.info(f"预约归还创建成功: appointment_id={appointment_id}")
        
        return jsonify({
            'success': True,
            'message': '预约归还申请已发送，等待失主确认',
            'data': {'appointment_id': appointment_id}
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"创建预约归还失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
