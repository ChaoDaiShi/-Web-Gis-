from flask import Blueprint, jsonify, request
import pymysql
import json
from datetime import datetime

appointment_items_bp = Blueprint('appointment_items', __name__)

CENTRAL_LOCATION_ID = 2

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='mapuser',
        password='123456',
        database='compus',
        charset='utf8mb4'
    )

@appointment_items_bp.route('/appointments/central-location', methods=['GET'])
def get_central_location():
    """获取集中点（失物招领处）信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT * FROM location WHERE location_id = %s
        """, (CENTRAL_LOCATION_ID,))
        
        location = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if location:
            return jsonify({'success': True, 'data': location})
        else:
            return jsonify({'success': False, 'message': '集中点不存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@appointment_items_bp.route('/appointments/central-items', methods=['GET'])
def get_central_items():
    """获取集中点（失物招领处）的拾物列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT li.*, u.username, u.avatar_url
            FROM lost_item li
            LEFT JOIN user u ON li.publisher_id = u.user_id
            WHERE li.location_id = %s AND li.status = 1
            ORDER BY li.create_time DESC
        """, (CENTRAL_LOCATION_ID,))
        
        items = cursor.fetchall()
        for item in items:
            if item['image_urls']:
                item['image_urls'] = json.loads(item['image_urls'])
            else:
                item['image_urls'] = []
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': items})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@appointment_items_bp.route('/appointments/publish-central', methods=['POST'])
def publish_to_central():
    """在集中点发布拾物信息"""
    data = request.json
    required_fields = ['title', 'description', 'type', 'publisher_id', 'image_urls']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        image_urls_json = json.dumps(data['image_urls']) if data['image_urls'] else None
        
        cursor.execute("""
            INSERT INTO lost_item (title, description, type, category_id, status, 
                                  image_urls, publisher_id, location_id, audit_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['title'],
            data['description'],
            data['type'],
            data.get('category_id'),
            1,
            image_urls_json,
            data['publisher_id'],
            CENTRAL_LOCATION_ID,
            'approved'
        ))
        
        conn.commit()
        item_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': {'item_id': item_id}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@appointment_items_bp.route('/appointments/available-items', methods=['GET'])
def get_available_items():
    """获取可预约的物品列表（集中点的拾物）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT li.*, u.username, u.avatar_url,
                   COUNT(a.appointment_id) as appointment_count
            FROM lost_item li
            LEFT JOIN user u ON li.publisher_id = u.user_id
            LEFT JOIN appointment a ON li.item_id = a.item_id AND a.status = 0
            WHERE li.location_id = %s AND li.status = 1 AND li.audit_status = 'approved'
            GROUP BY li.item_id
            ORDER BY li.create_time DESC
        """, (CENTRAL_LOCATION_ID,))
        
        items = cursor.fetchall()
        for item in items:
            if item['image_urls']:
                item['image_urls'] = json.loads(item['image_urls'])
            else:
                item['image_urls'] = []
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': items})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@appointment_items_bp.route('/appointments/item/<int:item_id>', methods=['GET'])
def get_item_appointments(item_id):
    """获取物品的预约列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT a.*, u.username, u.avatar_url
            FROM appointment a
            LEFT JOIN user u ON a.user_id = u.user_id
            WHERE a.item_id = %s
            ORDER BY a.create_time DESC
        """, (item_id,))
        
        appointments = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': appointments})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@appointment_items_bp.route('/appointments/book', methods=['POST'])
def book_appointment():
    """预约领取物品"""
    data = request.json
    required_fields = ['item_id', 'user_id', 'appointment_time']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO appointment (item_id, user_id, appointment_time, status, create_time)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data['item_id'],
            data['user_id'],
            data['appointment_time'],
            0,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        conn.commit()
        appointment_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': {'appointment_id': appointment_id}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@appointment_items_bp.route('/appointments/my-appointments', methods=['GET'])
def get_my_appointments():
    """获取当前用户的预约列表"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '缺少user_id参数'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT a.*, li.title, li.description, li.image_urls,
                   u.username as publisher_name, u.avatar_url as publisher_avatar
            FROM appointment a
            LEFT JOIN lost_item li ON a.item_id = li.item_id
            LEFT JOIN user u ON li.publisher_id = u.user_id
            WHERE a.user_id = %s
            ORDER BY a.create_time DESC
        """, (user_id,))
        
        appointments = cursor.fetchall()
        for app in appointments:
            if app['image_urls']:
                app['image_urls'] = json.loads(app['image_urls'])
            else:
                app['image_urls'] = []
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': appointments})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@appointment_items_bp.route('/appointments/<int:appointment_id>/confirm', methods=['POST'])
def confirm_appointment(appointment_id):
    """确认预约（管理员操作）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE appointment SET status = 1, update_time = %s
            WHERE appointment_id = %s
        """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), appointment_id))
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@appointment_items_bp.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
def cancel_appointment(appointment_id):
    """取消预约"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE appointment SET status = 2, update_time = %s
            WHERE appointment_id = %s
        """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), appointment_id))
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
