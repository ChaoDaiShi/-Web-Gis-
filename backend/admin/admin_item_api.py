from flask import Blueprint, request, jsonify
from datetime import datetime
import pymysql
import json
from admin.admin_common import get_conn, admin_required

admin_item_api_bp = Blueprint('admin_item_api', __name__)

@admin_item_api_bp.route('/items/audit', methods=['GET'])
@admin_required
def get_pending_items():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        audit_status = request.args.get('audit_status', 'pending')
        
        cursor.execute("SELECT COUNT(*) FROM lost_item WHERE audit_status = %s", (audit_status,))
        total = cursor.fetchone()['COUNT(*)']
        
        offset = (page - 1) * per_page
        cursor.execute("""
            SELECT * FROM lost_item 
            WHERE audit_status = %s 
            ORDER BY create_time DESC 
            LIMIT %s OFFSET %s
        """, (audit_status, per_page, offset))
        items = cursor.fetchall()
        
        pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'items': items,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': pages
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_item_api_bp.route('/items/<item_id>/audit', methods=['POST'])
@admin_required
def audit_item(item_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT title, publisher_id FROM lost_item WHERE item_id = %s", (item_id,))
        item = cursor.fetchone()
        
        if not item:
            return jsonify({'code': 404, 'message': '物品不存在'}), 404
        
        item_title = item[0]
        publisher_id = item[1]
        
        data = request.get_json()
        audit_status = data.get('audit_status')
        audit_remark = data.get('audit_remark', '')
        
        print(f"[DEBUG] audit_item - item_id: {item_id}, audit_status: {audit_status}, audit_remark: {audit_remark}")
        
        if audit_status not in ['approved', 'rejected']:
            return jsonify({'code': 400, 'message': '无效的审核状态'}), 400
        
        updates = [
            "audit_status = %s",
            "audit_time = %s",
            "audit_remark = %s"
        ]
        params = [audit_status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), audit_remark]
        
        if audit_status == 'approved':
            updates.append("status = 0")
        
        query = "UPDATE lost_item SET " + ", ".join(updates) + " WHERE item_id = %s"
        params.append(item_id)
        
        print(f"[DEBUG] audit_item - SQL: {query}, params: {params}")
        
        cursor.execute(query, params)
        affected_rows = cursor.rowcount
        print(f"[DEBUG] audit_item - affected_rows: {affected_rows}")
        
        conn.commit()
        print(f"[DEBUG] audit_item - commit successful")
        
        notification_conn = None
        notification_cursor = None
        try:
            notification_conn = get_conn()
            notification_cursor = notification_conn.cursor()
            
            item_name = item_title or '未知物品'
            
            if audit_status == 'approved':
                title = f"{item_name}发布审核通过"
                content = f"您发布的「物品ID：{item_id}，物品名：{item_name}」已通过审核，现在其他用户可以在地图上看到该物品了。"
                if audit_remark:
                    content += f" 审核备注：{audit_remark}"
            else:
                title = f"{item_name}发布审核未通过"
                content = f"您发布的「物品ID：{item_id}，物品名：{item_name}」未通过审核，请检查物品信息是否完整或重新提交。"
                if audit_remark:
                    content += f" 拒绝原因：{audit_remark}"
            
            local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            notification_cursor.execute("""
                INSERT INTO messages (user_id, title, content, message_type, create_time, is_read, is_deleted)
                VALUES (%s, %s, %s, 'audit', %s, FALSE, FALSE)
            """, (publisher_id, title, content, local_time))
            
            notification_conn.commit()
            print(f"[DEBUG] 审核通知已发送给用户 {publisher_id}")
        except Exception as e:
            print(f"发送审核通知失败: {e}")
            if notification_conn:
                notification_conn.rollback()
        finally:
            if notification_cursor:
                notification_cursor.close()
            if notification_conn:
                notification_conn.close()
        
        return jsonify({
            'code': 200,
            'message': '审核成功'
        })
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_item_api_bp.route('/lost_items', methods=['GET'])
def get_lost_items():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        audit_status = request.args.get('audit_status')
        
        if audit_status:
            cursor.execute("SELECT * FROM lost_item WHERE audit_status = %s", (audit_status,))
        else:
            cursor.execute("SELECT * FROM lost_item")
        items = cursor.fetchall()
        
        result = []
        for item in items:
            image_urls = []
            if item.get('image_urls'):
                try:
                    image_urls = json.loads(item['image_urls'])
                except:
                    image_urls = []
            
            item_type = item.get('type')
            item_status = item.get('status')
            publish_time = item.get('publish_time') or item.get('create_time')
            
            result.append({
                'item_id': item['item_id'],
                'title': item['title'],
                'description': item.get('description', ''),
                'item_type': '招领' if item_type == 1 else '丢失',
                'type': '拾到' if item_type == 1 else '丢失',
                'category_id': item.get('category_id'),
                'status': ['待认领', '已认领', '已关闭'][item_status] if item_status is not None else '未知',
                'audit_status': item.get('audit_status', 'pending'),
                'image_urls': image_urls,
                'publisher_id': item.get('publisher_id'),
                'location_id': item.get('location_id'),
                'create_time': item['create_time'].strftime('%Y-%m-%d %H:%M:%S') if item.get('create_time') else '',
                'publish_time': publish_time.strftime('%Y-%m-%d %H:%M:%S') if publish_time else '',
                'update_time': item['update_time'].strftime('%Y-%m-%d %H:%M:%S') if item.get('update_time') else ''
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_item_api_bp.route('/lost_items', methods=['POST'])
def add_lost_item():
    data = request.get_json()
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        image_urls = json.dumps(data.get('image_urls', []))
        
        cursor.execute("""
            INSERT INTO lost_item (title, description, type, category_id, status, image_urls, publisher_id, location_id, create_time, update_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['title'],
            data.get('description', ''),
            int(data.get('type', 0)),
            int(data.get('category_id', 0)),
            int(data.get('status', 0)),
            image_urls,
            int(data.get('publisher_id', 0)),
            int(data.get('location_id', 0)),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        item_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({'success': True, 'message': '添加成功', 'item_id': item_id})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_item_api_bp.route('/lost_items/<int:item_id>', methods=['PUT'])
def update_lost_item(item_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM lost_item WHERE item_id = %s", (item_id,))
        item = cursor.fetchone()
        
        if not item:
            return jsonify({'success': False, 'message': '记录不存在'})
        
        data = request.get_json()
        
        updates = []
        params = []
        
        if 'title' in data:
            updates.append("title = %s")
            params.append(data['title'])
        if 'description' in data:
            updates.append("description = %s")
            params.append(data['description'])
        if 'type' in data:
            updates.append("type = %s")
            params.append(int(data['type']))
        if 'category_id' in data:
            updates.append("category_id = %s")
            params.append(int(data['category_id']))
        if 'status' in data:
            updates.append("status = %s")
            params.append(int(data['status']))
        if 'image_urls' in data:
            updates.append("image_urls = %s")
            params.append(json.dumps(data['image_urls']))
        if 'publisher_id' in data:
            updates.append("publisher_id = %s")
            params.append(int(data['publisher_id']))
        if 'location_id' in data:
            updates.append("location_id = %s")
            params.append(int(data['location_id']))
        
        updates.append("update_time = %s")
        params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        query = "UPDATE lost_item SET " + ", ".join(updates) + " WHERE item_id = %s"
        params.append(item_id)
        
        cursor.execute(query, params)
        conn.commit()
        
        return jsonify({'success': True, 'message': '修改成功'})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_item_api_bp.route('/lost_items/<int:item_id>', methods=['DELETE'])
def delete_lost_item(item_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM lost_item WHERE item_id = %s", (item_id,))
        item = cursor.fetchone()
        
        if not item:
            return jsonify({'success': False, 'message': '记录不存在'})
        
        cursor.execute("DELETE FROM lost_item WHERE item_id = %s", (item_id,))
        conn.commit()
        
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()