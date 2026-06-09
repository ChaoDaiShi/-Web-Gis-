from flask import Blueprint, jsonify, request
from . import get_conn, logger

appointment_list_bp = Blueprint('appointment_list', __name__)

@appointment_list_bp.route('/appointments/list', methods=['GET'])
def get_appointment_list():
    logger.info("=== 获取预约列表 ===")
    user_id = request.args.get('user_id')
    status = request.args.get('status', 'all')
    item_id = request.args.get('item_id')
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        sql = """
            SELECT 
                a.appointment_id,
                a.item_id,
                a.user_id,
                a.appointment_time,
                a.location,
                a.longitude,
                a.latitude,
                a.contact_name,
                a.contact_phone,
                a.note,
                a.status,
                a.create_time,
                a.update_time,
                l.title as item_title,
                l.description as item_description,
                u.username,
                u.avatar_url
            FROM appointment a
            LEFT JOIN lost_item l ON a.item_id = l.item_id
            LEFT JOIN user u ON a.user_id = u.user_id
            WHERE 1=1
        """
        params = []
        
        if user_id:
            sql += " AND a.user_id = %s"
            params.append(user_id)
        
        if item_id:
            sql += " AND a.item_id = %s"
            params.append(item_id)
        
        if status != 'all':
            sql += " AND a.status = %s"
            params.append(status)
        
        sql += " ORDER BY a.create_time DESC"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        appointments = []
        for row in rows:
            appointments.append({
                'appointment_id': row[0],
                'item_id': row[1],
                'user_id': row[2],
                'appointment_time': row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] else None,
                'location': row[4],
                'longitude': float(row[5]) if row[5] else None,
                'latitude': float(row[6]) if row[6] else None,
                'contact_name': row[7],
                'contact_phone': row[8],
                'note': row[9],
                'status': row[10],
                'create_time': row[11].strftime('%Y-%m-%d %H:%M:%S') if row[11] else None,
                'update_time': row[12].strftime('%Y-%m-%d %H:%M:%S') if row[12] else None,
                'item_title': row[13],
                'item_description': row[14],
                'username': row[15],
                'avatar_url': row[16]
            })
        
        logger.info(f"查询到 {len(appointments)} 条预约记录")
        
        return jsonify({
            "success": True,
            "data": appointments
        })
        
    except Exception as e:
        logger.error(f"获取预约列表失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@appointment_list_bp.route('/appointments/my', methods=['GET'])
def get_my_appointments():
    logger.info("=== 获取我的预约 ===")
    user_id = request.args.get('user_id')
    
    if not user_id:
        logger.warning("获取我的预约失败: 缺少user_id")
        return jsonify({"success": False, "message": "缺少用户ID"}), 400
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                a.appointment_id,
                a.item_id,
                a.appointment_time,
                a.location,
                a.longitude,
                a.latitude,
                a.contact_name,
                a.contact_phone,
                a.note,
                a.status,
                a.create_time,
                l.title as item_title,
                l.description as item_description,
                l.image_urls as images
            FROM appointment a
            LEFT JOIN lost_item l ON a.item_id = l.item_id
            WHERE a.user_id = %s
            ORDER BY a.create_time DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        
        appointments = []
        for row in rows:
            appointments.append({
                'appointment_id': row[0],
                'item_id': row[1],
                'appointment_time': row[2].strftime('%Y-%m-%d %H:%M:%S') if row[2] else None,
                'location': row[3],
                'longitude': float(row[4]) if row[4] else None,
                'latitude': float(row[5]) if row[5] else None,
                'contact_name': row[6],
                'contact_phone': row[7],
                'note': row[8],
                'status': row[9],
                'create_time': row[10].strftime('%Y-%m-%d %H:%M:%S') if row[10] else None,
                'item_title': row[11],
                'item_description': row[12],
                'item_images': row[13]
            })
        
        logger.info(f"查询到 {len(appointments)} 条我的预约记录")
        
        return jsonify({
            "success": True,
            "data": appointments
        })
        
    except Exception as e:
        logger.error(f"获取我的预约失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
