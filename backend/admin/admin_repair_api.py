from flask import Blueprint, request, jsonify
import pymysql
from admin.admin_common import get_conn, admin_required

admin_repair_api_bp = Blueprint('admin_repair_api', __name__)

@admin_repair_api_bp.route('/repair-list', methods=['GET'])
@admin_required
def get_repair_list():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', type=int)
        
        query = """
            SELECT r.*, rc.name as category_name, u.username as reporter_name
            FROM repair r
            LEFT JOIN repair_category rc ON r.repair_category_id = rc.repair_category_id
            LEFT JOIN user u ON r.reporter_id = u.user_id
            WHERE 1=1
        """
        params = []
        
        if status is not None:
            query += " AND r.status = %s"
            params.append(status)
        
        count_query = query.replace("SELECT r.*, rc.name as category_name, u.username as reporter_name", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total = cursor.fetchone()['COUNT(*)']
        
        offset = (page - 1) * per_page
        query += " ORDER BY r.create_time DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        repairs = []
        for row in results:
            repairs.append({
                'repair_id': row['repair_id'],
                'title': row['title'],
                'description': row['description'],
                'repair_category_id': row['repair_category_id'],
                'category_name': row['category_name'],
                'location_id': row['location_id'],
                'reporter_id': row['reporter_id'],
                'reporter_name': row['reporter_name'],
                'images': row['images'],
                'status': row['status'],
                'priority': row['priority'],
                'assignee_id': row['assignee_id'],
                'process_note': row['process_note'],
                'create_time': row['create_time'].strftime('%Y-%m-%d %H:%M:%S') if row.get('create_time') else None,
                'update_time': row['update_time'].strftime('%Y-%m-%d %H:%M:%S') if row.get('update_time') else None
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'repairs': repairs,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_repair_api_bp.route('/repair/<int:repair_id>', methods=['GET'])
@admin_required
def get_repair_detail(repair_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT r.*, rc.name as category_name, u.username as reporter_name
            FROM repair r
            LEFT JOIN repair_category rc ON r.repair_category_id = rc.repair_category_id
            LEFT JOIN user u ON r.reporter_id = u.user_id
            WHERE r.repair_id = %s
        """, (repair_id,))
        
        row = cursor.fetchone()
        if not row:
            return jsonify({'code': 404, 'message': '报修记录不存在'}), 404
        
        repair = {
            'repair_id': row['repair_id'],
            'title': row['title'],
            'description': row['description'],
            'repair_category_id': row['repair_category_id'],
            'category_name': row['category_name'],
            'location_id': row['location_id'],
            'reporter_id': row['reporter_id'],
            'reporter_name': row['reporter_name'],
            'images': row['images'],
            'status': row['status'],
            'priority': row['priority'],
            'assignee_id': row['assignee_id'],
            'process_note': row['process_note'],
            'create_time': row['create_time'].strftime('%Y-%m-%d %H:%M:%S') if row.get('create_time') else None,
            'update_time': row['update_time'].strftime('%Y-%m-%d %H:%M:%S') if row.get('update_time') else None
        }
        
        return jsonify({'code': 200, 'message': 'success', 'data': repair})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_repair_api_bp.route('/repair/<int:repair_id>', methods=['PUT'])
@admin_required
def update_repair(repair_id):
    conn = None
    cursor = None
    try:
        data = request.get_json() or {}
        
        conn = get_conn()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if 'title' in data:
            updates.append("title = %s")
            params.append(data['title'])
        if 'description' in data:
            updates.append("description = %s")
            params.append(data['description'])
        if 'status' in data:
            updates.append("status = %s")
            params.append(data['status'])
        if 'priority' in data:
            updates.append("priority = %s")
            params.append(data['priority'])
        if 'assignee_id' in data:
            updates.append("assignee_id = %s")
            params.append(data['assignee_id'])
        if 'process_note' in data:
            updates.append("process_note = %s")
            params.append(data['process_note'])
        
        if not updates:
            return jsonify({'code': 400, 'message': '没有提供更新字段'}), 400
        
        params.append(repair_id)
        query = "UPDATE repair SET " + ", ".join(updates) + " WHERE repair_id = %s"
        
        cursor.execute(query, params)
        conn.commit()
        
        return jsonify({'code': 200, 'message': '更新成功'})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_repair_api_bp.route('/repair/<int:repair_id>', methods=['DELETE'])
@admin_required
def delete_repair(repair_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM repair WHERE repair_id = %s", (repair_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'code': 404, 'message': '报修记录不存在'}), 404
        
        return jsonify({'code': 200, 'message': '删除成功'})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_repair_api_bp.route('/repair-categories', methods=['GET'])
@admin_required
def get_repair_categories():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT * FROM repair_category ORDER BY repair_category_id")
        results = cursor.fetchall()
        
        categories = []
        for row in results:
            categories.append({
                'repair_category_id': row['repair_category_id'],
                'name': row['name'],
                'icon': row['icon'],
                'description': row['description']
            })
        
        return jsonify({'code': 200, 'message': 'success', 'data': categories})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()