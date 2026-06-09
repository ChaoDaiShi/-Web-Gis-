from flask import Blueprint, jsonify, request
from admin.admin_common import get_conn, admin_required, super_admin_required
from datetime import datetime
import hashlib
import json
import pymysql

admin_admin_api_bp = Blueprint('admin_admin_api', __name__)

@admin_admin_api_bp.route('/admins', methods=['GET'])
@admin_required
def get_admins():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute('SELECT admin_id, username, role, department, permission_type, permissions, create_time FROM admin')
        admins = cursor.fetchall()
        
        return jsonify({'success': True, 'data': admins})
    except Exception as e:
        print(f"获取管理员列表失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_admin_api_bp.route('/admins', methods=['POST'])
@super_admin_required
def create_admin():
    print("DEBUG create_admin - Function called")
    conn = None
    cursor = None
    try:
        data = request.get_json()
        print(f"DEBUG create_admin - Request data: {data}")
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'secondary_admin')
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute('SELECT admin_id FROM admin WHERE username = %s', (username,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO admin (username, password_hash, role, create_time)
            VALUES (%s, %s, %s, %s)
        ''', (username, password_hash, role, create_time))
        
        conn.commit()
        return jsonify({'success': True, 'message': '管理员创建成功'})
    except Exception as e:
        print(f"创建管理员失败: {e}")
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_admin_api_bp.route('/admins/<int:admin_id>', methods=['GET'])
@admin_required
def get_admin(admin_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute('SELECT admin_id, username, role, department, permission_type, permissions, create_time FROM admin WHERE admin_id = %s', (admin_id,))
        admin = cursor.fetchone()
        
        if not admin:
            return jsonify({'success': False, 'message': '管理员不存在'}), 404
        
        return jsonify({'success': True, 'data': admin})
    except Exception as e:
        print(f"获取管理员信息失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_admin_api_bp.route('/admins/<int:admin_id>', methods=['PUT'])
@super_admin_required
def update_admin(admin_id):
    conn = None
    cursor = None
    try:
        data = request.get_json()
        
        conn = get_conn()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if 'role' in data:
            updates.append('role = %s')
            params.append(data['role'])
        if 'department' in data:
            updates.append('department = %s')
            params.append(data['department'])
        if 'permission_type' in data:
            updates.append('permission_type = %s')
            params.append(data['permission_type'])
        
        if not updates:
            return jsonify({'success': False, 'message': '没有要更新的字段'}), 400
        
        params.append(admin_id)
        cursor.execute(f'UPDATE admin SET {", ".join(updates)} WHERE admin_id = %s', params)
        
        conn.commit()
        return jsonify({'success': True, 'message': '更新成功'})
    except Exception as e:
        print(f"更新管理员信息失败: {e}")
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_admin_api_bp.route('/admins/<int:admin_id>', methods=['DELETE'])
@super_admin_required
def delete_admin(admin_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute('SELECT role FROM admin WHERE admin_id = %s', (admin_id,))
        admin = cursor.fetchone()
        if admin and admin[0] == 'super_admin':
            return jsonify({'success': False, 'message': '不能删除超级管理员'}), 403
        
        cursor.execute('DELETE FROM admin WHERE admin_id = %s', (admin_id,))
        
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': '管理员不存在'}), 404
        
        conn.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        print(f"删除管理员失败: {e}")
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_admin_api_bp.route('/admins/<int:admin_id>/permissions', methods=['PUT'])
@super_admin_required
def update_admin_permissions(admin_id):
    conn = None
    cursor = None
    try:
        data = request.get_json()
        permissions = data.get('permissions', [])
        
        conn = get_conn()
        cursor = conn.cursor()
        
        permissions_json = json.dumps(permissions)
        cursor.execute('UPDATE admin SET permissions = %s WHERE admin_id = %s', (permissions_json, admin_id))
        
        conn.commit()
        return jsonify({'success': True, 'message': '权限更新成功'})
    except Exception as e:
        print(f"更新管理员权限失败: {e}")
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_admin_api_bp.route('/permissions', methods=['GET'])
@admin_required
def get_permissions():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute('SELECT * FROM permission_definition ORDER BY category, permission_id')
        permissions = cursor.fetchall()
        
        return jsonify({'success': True, 'data': permissions})
    except Exception as e:
        print(f"获取权限定义失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_admin_api_bp.route('/privilege-requests', methods=['GET'])
@super_admin_required
def get_privilege_requests():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute('''
            SELECT pr.*, a.username as admin_username 
            FROM privilege_request pr
            LEFT JOIN admin a ON pr.admin_id = a.admin_id
            ORDER BY pr.create_time DESC
        ''')
        requests = cursor.fetchall()
        
        return jsonify({'success': True, 'data': requests})
    except Exception as e:
        print(f"获取权限申请列表失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_admin_api_bp.route('/privilege-requests/<int:request_id>/approve', methods=['POST'])
@super_admin_required
def approve_privilege_request(request_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute('SELECT admin_id, requested_permissions FROM privilege_request WHERE request_id = %s AND status = "pending"', (request_id,))
        request_data = cursor.fetchone()
        
        if not request_data:
            return jsonify({'success': False, 'message': '申请不存在或已处理'}), 400
        
        admin_id = request_data['admin_id']
        requested_permissions = request_data['requested_permissions']
        
        cursor.execute('SELECT permissions FROM admin WHERE admin_id = %s', (admin_id,))
        admin = cursor.fetchone()
        
        if admin and admin['permissions']:
            current_perms = json.loads(admin['permissions'])
        else:
            current_perms = []
        
        new_perms = json.loads(requested_permissions)
        updated_perms = list(set(current_perms + new_perms))
        
        cursor.execute('UPDATE admin SET permissions = %s WHERE admin_id = %s', (json.dumps(updated_perms), admin_id))
        
        cursor.execute('UPDATE privilege_request SET status = "approved", review_time = %s WHERE request_id = %s', 
                      (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), request_id))
        
        conn.commit()
        return jsonify({'success': True, 'message': '权限申请已批准'})
    except Exception as e:
        print(f"批准权限申请失败: {e}")
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_admin_api_bp.route('/privilege-requests/<int:request_id>/reject', methods=['POST'])
@super_admin_required
def reject_privilege_request(request_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE privilege_request SET status = "rejected", review_time = %s WHERE request_id = %s AND status = "pending"', 
                      (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), request_id))
        
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': '申请不存在或已处理'}), 400
        
        conn.commit()
        return jsonify({'success': True, 'message': '权限申请已拒绝'})
    except Exception as e:
        print(f"拒绝权限申请失败: {e}")
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
