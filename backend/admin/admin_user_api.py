from flask import Blueprint, request, jsonify
from datetime import datetime
import pymysql
from admin.admin_common import get_conn, admin_required

admin_user_api_bp = Blueprint('admin_user_api', __name__)

@admin_user_api_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        keyword = request.args.get('keyword', '')
        role = request.args.get('role', '')
        status = request.args.get('status', '')
        
        query = "SELECT * FROM user WHERE 1=1"
        params = []
        
        if keyword:
            query += " AND (username LIKE %s OR phone LIKE %s OR email LIKE %s)"
            params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
        
        if role:
            query += " AND role = %s"
            params.append(role)
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        query += " ORDER BY create_time DESC"
        
        total_query = "SELECT COUNT(*) FROM user WHERE 1=1"
        total_params = []
        if keyword:
            total_query += " AND (username LIKE %s OR phone LIKE %s OR email LIKE %s)"
            total_params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
        if role:
            total_query += " AND role = %s"
            total_params.append(role)
        if status:
            total_query += " AND status = %s"
            total_params.append(status)
        
        cursor.execute(total_query, total_params)
        total = cursor.fetchone()['COUNT(*)']
        
        offset = (page - 1) * per_page
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        
        pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'users': users,
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

@admin_user_api_bp.route('/users/<user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM user WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        data = request.get_json()
        
        updates = []
        params = []
        
        if 'role' in data:
            updates.append("role = %s")
            params.append(data['role'])
        if 'status' in data:
            updates.append("status = %s")
            params.append(data['status'])
        if 'phone' in data:
            updates.append("phone = %s")
            params.append(data['phone'])
        if 'email' in data:
            updates.append("email = %s")
            params.append(data['email'])
        
        if updates:
            query = "UPDATE user SET " + ", ".join(updates) + " WHERE user_id = %s"
            params.append(user_id)
            cursor.execute(query, params)
            conn.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新成功'
        })
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_user_api_bp.route('/users/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT username, role FROM user WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        if user[1] == 'super_admin':
            return jsonify({'code': 403, 'message': '不能删除超级管理员'}), 403
        
        username = user[0]
        cursor.execute("DELETE FROM user WHERE user_id = %s", (user_id,))
        conn.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功'
        })
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()