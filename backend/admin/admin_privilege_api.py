from flask import Blueprint, request, jsonify
from datetime import datetime
import pymysql
import json
from admin.admin_common import get_conn, admin_required, super_admin_required, permission_required, get_admin_permissions

admin_privilege_api_bp = Blueprint('admin_privilege_api', __name__)

@admin_privilege_api_bp.route('/permissions', methods=['GET'])
@admin_required
def get_permission_definitions():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT permission_key, permission_name, description, category
            FROM permission_definition
            ORDER BY category, permission_id
        """)
        
        permissions = cursor.fetchall()
        
        return jsonify({
            'code': 200,
            'data': permissions
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_privilege_api_bp.route('/secondary-admins', methods=['GET'])
@admin_required
def get_secondary_admins():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT admin_id, username, role, permissions, department, permission_type, create_time
            FROM admin
            WHERE role = 'secondary_admin'
            ORDER BY create_time DESC
        """)
        
        admins = cursor.fetchall()
        
        for admin in admins:
            if admin['permissions']:
                try:
                    admin['permissions'] = json.loads(admin['permissions'])
                except:
                    admin['permissions'] = []
            else:
                admin['permissions'] = []
            
            if admin['create_time']:
                admin['create_time'] = admin['create_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'code': 200,
            'data': admins
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_privilege_api_bp.route('/privilege-requests', methods=['GET'])
@admin_required
def get_privilege_requests():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        current_admin = getattr(request, 'current_admin', None)
        if not current_admin:
            return jsonify({'code': 401, 'message': '未授权'}), 401
        
        status_filter = request.args.get('status', '')
        
        if current_admin.get('role') == 'super_admin':
            if status_filter:
                cursor.execute("""
                    SELECT pr.*, 
                           a.username as applicant_name,
                           a.department as applicant_department,
                           r.username as reviewer_name,
                           t.username as target_admin_name,
                           t.department as target_admin_department
                    FROM privilege_request pr
                    LEFT JOIN admin a ON pr.admin_id = a.admin_id
                    LEFT JOIN admin r ON pr.reviewer_id = r.admin_id
                    LEFT JOIN admin t ON pr.target_admin_id = t.admin_id
                    WHERE pr.status = %s
                    ORDER BY pr.create_time DESC
                """, (status_filter,))
            else:
                cursor.execute("""
                    SELECT pr.*, 
                           a.username as applicant_name,
                           a.department as applicant_department,
                           r.username as reviewer_name,
                           t.username as target_admin_name,
                           t.department as target_admin_department
                    FROM privilege_request pr
                    LEFT JOIN admin a ON pr.admin_id = a.admin_id
                    LEFT JOIN admin r ON pr.reviewer_id = r.admin_id
                    LEFT JOIN admin t ON pr.target_admin_id = t.admin_id
                    ORDER BY pr.create_time DESC
                """)
        else:
            if status_filter:
                cursor.execute("""
                    SELECT pr.*, 
                           a.username as applicant_name,
                           a.department as applicant_department,
                           r.username as reviewer_name,
                           t.username as target_admin_name,
                           t.department as target_admin_department
                    FROM privilege_request pr
                    LEFT JOIN admin a ON pr.admin_id = a.admin_id
                    LEFT JOIN admin r ON pr.reviewer_id = r.admin_id
                    LEFT JOIN admin t ON pr.target_admin_id = t.admin_id
                    WHERE pr.admin_id = %s AND pr.status = %s
                    ORDER BY pr.create_time DESC
                """, (current_admin['admin_id'], status_filter))
            else:
                cursor.execute("""
                    SELECT pr.*, 
                           a.username as applicant_name,
                           a.department as applicant_department,
                           r.username as reviewer_name,
                           t.username as target_admin_name,
                           t.department as target_admin_department
                    FROM privilege_request pr
                    LEFT JOIN admin a ON pr.admin_id = a.admin_id
                    LEFT JOIN admin r ON pr.reviewer_id = r.admin_id
                    LEFT JOIN admin t ON pr.target_admin_id = t.admin_id
                    WHERE pr.admin_id = %s
                    ORDER BY pr.create_time DESC
                """, (current_admin['admin_id'],))
        
        requests = cursor.fetchall()
        
        for req in requests:
            if req['create_time']:
                req['create_time'] = req['create_time'].strftime('%Y-%m-%d %H:%M:%S')
            if req['review_time']:
                req['review_time'] = req['review_time'].strftime('%Y-%m-%d %H:%M:%S')
            
            if req['requested_permissions']:
                try:
                    req['requested_permissions'] = json.loads(req['requested_permissions'])
                except:
                    req['requested_permissions'] = []
            else:
                req['requested_permissions'] = []
        
        return jsonify({
            'code': 200,
            'data': requests
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_privilege_api_bp.route('/privilege-requests', methods=['POST'])
@admin_required
def create_privilege_request():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        current_admin = getattr(request, 'current_admin', None)
        if not current_admin:
            return jsonify({'code': 401, 'message': '未授权'}), 401
        
        data = request.get_json()
        reason = data.get('reason', '').strip()
        requested_permissions = data.get('requested_permissions', [])
        target_admin_id = data.get('target_admin_id')
        
        if not reason:
            return jsonify({'code': 400, 'message': '请填写申请理由'}), 400
        
        if not requested_permissions:
            return jsonify({'code': 400, 'message': '请选择申请的权限'}), 400
        
        if not target_admin_id:
            return jsonify({'code': 400, 'message': '请选择目标管理员'}), 400
        
        cursor.execute("SELECT role FROM admin WHERE admin_id = %s", (current_admin['admin_id'],))
        admin_info = cursor.fetchone()
        
        if not admin_info:
            return jsonify({'code': 404, 'message': '管理员不存在'}), 404
        
        if admin_info['role'] == 'super_admin':
            return jsonify({'code': 400, 'message': '您已经是超级管理员'}), 400
        
        cursor.execute("SELECT admin_id FROM admin WHERE admin_id = %s AND role = 'secondary_admin'", (target_admin_id,))
        if not cursor.fetchone():
            return jsonify({'code': 404, 'message': '目标管理员不存在或不是二级管理员'}), 404
        
        cursor.execute("""
            SELECT * FROM privilege_request 
            WHERE admin_id = %s AND status = 'pending'
        """, (current_admin['admin_id'],))
        
        if cursor.fetchone():
            return jsonify({'code': 400, 'message': '您已有待审核的申请'}), 400
        
        permissions_json = json.dumps(requested_permissions)
        
        cursor.execute("""
            INSERT INTO privilege_request (admin_id, reason, status, create_time, requested_permissions, target_admin_id)
            VALUES (%s, %s, 'pending', NOW(), %s, %s)
        """, (current_admin['admin_id'], reason, permissions_json, target_admin_id))
        conn.commit()
        
        return jsonify({
            'code': 200,
            'message': '提权申请已提交'
        })
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_privilege_api_bp.route('/privilege-requests/<int:request_id>/approve', methods=['POST'])
@super_admin_required
def approve_privilege_request(request_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        current_admin = getattr(request, 'current_admin', None)
        
        cursor.execute("SELECT * FROM privilege_request WHERE request_id = %s", (request_id,))
        pr = cursor.fetchone()
        
        if not pr:
            return jsonify({'code': 404, 'message': '申请不存在'}), 404
        
        if pr['status'] != 'pending':
            return jsonify({'code': 400, 'message': '该申请已处理'}), 400
        
        data = request.get_json() or {}
        review_note = data.get('review_note', '').strip()
        approved_permissions = data.get('approved_permissions', [])
        
        if not approved_permissions and pr['requested_permissions']:
            try:
                approved_permissions = json.loads(pr['requested_permissions'])
            except:
                approved_permissions = []
        
        permissions_json = json.dumps(approved_permissions) if approved_permissions else None
        
        cursor.execute("""
            UPDATE privilege_request 
            SET status = 'approved', 
                reviewer_id = %s, 
                review_time = NOW(),
                review_note = %s
            WHERE request_id = %s
        """, (current_admin['admin_id'], review_note, request_id))
        
        if permissions_json:
            cursor.execute("""
                UPDATE admin SET permissions = %s 
                WHERE admin_id = %s
            """, (permissions_json, pr['admin_id']))
        
        conn.commit()
        
        return jsonify({
            'code': 200,
            'message': '提权申请已通过，权限已分配'
        })
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_privilege_api_bp.route('/privilege-requests/<int:request_id>/reject', methods=['POST'])
@super_admin_required
def reject_privilege_request(request_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        current_admin = getattr(request, 'current_admin', None)
        
        cursor.execute("SELECT * FROM privilege_request WHERE request_id = %s", (request_id,))
        pr = cursor.fetchone()
        
        if not pr:
            return jsonify({'code': 404, 'message': '申请不存在'}), 404
        
        if pr['status'] != 'pending':
            return jsonify({'code': 400, 'message': '该申请已处理'}), 400
        
        data = request.get_json() or {}
        review_note = data.get('review_note', '').strip()
        
        cursor.execute("""
            UPDATE privilege_request 
            SET status = 'rejected', 
                reviewer_id = %s, 
                review_time = NOW(),
                review_note = %s
            WHERE request_id = %s
        """, (current_admin['admin_id'], review_note, request_id))
        
        conn.commit()
        
        return jsonify({
            'code': 200,
            'message': '提权申请已拒绝'
        })
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_privilege_api_bp.route('/admins', methods=['GET'])
@super_admin_required
def get_all_admins():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT admin_id, username, role, permissions, department, permission_type, create_time, last_login
            FROM admin
            ORDER BY create_time DESC
        """)
        
        admins = cursor.fetchall()
        
        for admin in admins:
            if admin['permissions']:
                try:
                    admin['permissions'] = json.loads(admin['permissions'])
                except:
                    admin['permissions'] = []
            else:
                admin['permissions'] = []
            
            if admin['create_time']:
                admin['create_time'] = admin['create_time'].strftime('%Y-%m-%d %H:%M:%S')
            if admin['last_login']:
                admin['last_login'] = admin['last_login'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'code': 200,
            'data': admins
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_privilege_api_bp.route('/admins', methods=['POST'])
@super_admin_required
def create_admin():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'secondary_admin').strip()
        permissions = data.get('permissions', [])
        department = data.get('department', '').strip()
        permission_type = data.get('permission_type', 'general').strip()
        
        if not username or not password:
            return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400
        
        if role not in ['super_admin', 'secondary_admin']:
            return jsonify({'code': 400, 'message': '无效的角色类型'}), 400
        
        cursor.execute("SELECT * FROM admin WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({'code': 400, 'message': '用户名已存在'}), 400
        
        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash(password)
        
        permissions_json = json.dumps(permissions) if permissions else None
        
        cursor.execute("""
            INSERT INTO admin (username, password_hash, role, permissions, department, permission_type, create_time)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (username, hashed_password, role, permissions_json, department, permission_type))
        conn.commit()
        
        return jsonify({
            'code': 200,
            'message': '管理员创建成功'
        })
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_privilege_api_bp.route('/admins/<int:admin_id>', methods=['DELETE'])
@super_admin_required
def delete_admin(admin_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        current_admin = getattr(request, 'current_admin', None)
        
        if current_admin and admin_id == current_admin['admin_id']:
            return jsonify({'code': 400, 'message': '不能删除自己的账号'}), 400
        
        cursor.execute("SELECT * FROM admin WHERE admin_id = %s", (admin_id,))
        admin = cursor.fetchone()
        
        if not admin:
            return jsonify({'code': 404, 'message': '管理员不存在'}), 404
        
        cursor.execute("DELETE FROM privilege_request WHERE admin_id = %s", (admin_id,))
        cursor.execute("DELETE FROM admin WHERE admin_id = %s", (admin_id,))
        conn.commit()
        
        return jsonify({
            'code': 200,
            'message': '管理员删除成功'
        })
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_privilege_api_bp.route('/my-permissions', methods=['GET'])
@admin_required
def get_my_permissions():
    try:
        current_admin = getattr(request, 'current_admin', None)
        if not current_admin:
            return jsonify({'code': 401, 'message': '未授权'}), 401
        
        permissions = get_admin_permissions(current_admin['admin_id'])
        
        return jsonify({
            'code': 200,
            'data': {
                'role': current_admin.get('role'),
                'permissions': permissions,
                'department': current_admin.get('department'),
                'permission_type': current_admin.get('permission_type')
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
