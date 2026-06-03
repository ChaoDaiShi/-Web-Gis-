from flask import Blueprint, jsonify, request
from . import get_conn, logger

appointment_detail_bp = Blueprint('appointment_detail', __name__)

@appointment_detail_bp.route('/appointments/<int:appointment_id>', methods=['GET'])
def get_appointment_detail(appointment_id):
    logger.info(f"=== 获取预约详情: appointment_id={appointment_id} ===")
    
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
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
                a.reviewer_id,
                a.review_time,
                a.review_note,
                a.create_time,
                a.update_time,
                l.title as item_title,
                l.description as item_description,
                l.location as item_location,
                l.image_urls as item_images,
                l.status as item_status,
                u.username,
                u.avatar_url,
                u.email as user_email,
                u.phone as user_phone
            FROM appointment a
            LEFT JOIN lost_item l ON a.item_id = l.item_id
            LEFT JOIN user u ON a.user_id = u.user_id
            WHERE a.appointment_id = %s
        """, (appointment_id,))
        
        row = cursor.fetchone()
        
        if not row:
            logger.warning(f"预约不存在: appointment_id={appointment_id}")
            return jsonify({"success": False, "message": "预约不存在"}), 404
        
        appointment = {
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
            'reviewer_id': row[11],
            'review_time': row[12].strftime('%Y-%m-%d %H:%M:%S') if row[12] else None,
            'review_note': row[13],
            'create_time': row[14].strftime('%Y-%m-%d %H:%M:%S') if row[14] else None,
            'update_time': row[15].strftime('%Y-%m-%d %H:%M:%S') if row[15] else None,
            'item': {
                'title': row[16],
                'description': row[17],
                'location': row[18],
                'images': row[19],
                'status': row[20]
            },
            'user': {
                'username': row[21],
                'avatar_url': row[22],
                'email': row[23],
                'phone': row[24]
            }
        }
        
        logger.info(f"获取预约详情成功: appointment_id={appointment_id}")
        
        return jsonify({
            "success": True,
            "data": appointment
        })
        
    except Exception as e:
        logger.error(f"获取预约详情失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
