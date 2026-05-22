from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import pymysql

admin_full_bp = Blueprint('admin_full', __name__)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'mapuser',
    'password': '123456',
    'database': 'compus',
    'charset': 'utf8mb4'
}

def get_conn():
    return pymysql.connect(**DB_CONFIG)

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未授权'}), 401
        
        token = auth_header.replace('Bearer ', '')
        if token != 'admin_token':
            return jsonify({'code': 403, 'message': '需要管理员权限'}), 403
        
        return fn(*args, **kwargs)
    return wrapper

@admin_full_bp.route('/users', methods=['GET'])
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
        
        query = "SELECT * FROM users WHERE 1=1"
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
        
        query += " ORDER BY created_at DESC"
        
        total_query = "SELECT COUNT(*) FROM users WHERE 1=1"
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

@admin_full_bp.route('/users/<user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
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
            query = "UPDATE users SET " + ", ".join(updates) + " WHERE id = %s"
            params.append(user_id)
            cursor.execute(query, params)
            conn.commit()
        
        log_action('update_user', 'user', user_id, f'更新用户信息: {user[1]}')
        
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

@admin_full_bp.route('/users/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT username, role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        if user[1] == 'super_admin':
            return jsonify({'code': 403, 'message': '不能删除超级管理员'}), 403
        
        username = user[0]
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        
        log_action('delete_user', 'user', user_id, f'删除用户: {username}')
        
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

@admin_full_bp.route('/items/audit', methods=['GET'])
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
            ORDER BY publish_time DESC 
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

@admin_full_bp.route('/items/<item_id>/audit', methods=['POST'])
@admin_required
def audit_item(item_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT title FROM lost_item WHERE item_id = %s", (item_id,))
        item = cursor.fetchone()
        
        if not item:
            return jsonify({'code': 404, 'message': '物品不存在'}), 404
        
        data = request.get_json()
        audit_status = data.get('audit_status')
        audit_remark = data.get('audit_remark', '')
        
        if audit_status not in ['approved', 'rejected']:
            return jsonify({'code': 400, 'message': '无效的审核状态'}), 400
        
        updates = [
            "audit_status = %s",
            "audit_time = %s",
            "audit_remark = %s"
        ]
        params = [audit_status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), audit_remark]
        
        if audit_status == 'approved':
            updates.append("status = 'pending'")
        
        query = "UPDATE lost_item SET " + ", ".join(updates) + " WHERE item_id = %s"
        params.append(item_id)
        
        cursor.execute(query, params)
        conn.commit()
        
        log_action('audit_item', 'lost_item', item_id, f'审核物品: {item[0]}, 结果: {audit_status}')
        
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

@admin_full_bp.route('/claims/audit', methods=['GET'])
@admin_required
def get_pending_claims():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status = request.args.get('status', 'pending')
        
        cursor.execute("SELECT COUNT(*) FROM claim_form WHERE status = %s", (status,))
        total = cursor.fetchone()['COUNT(*)']
        
        offset = (page - 1) * per_page
        cursor.execute("""
            SELECT * FROM claim_form 
            WHERE status = %s 
            ORDER BY create_time DESC 
            LIMIT %s OFFSET %s
        """, (status, per_page, offset))
        claims = cursor.fetchall()
        
        pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'claims': claims,
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

@admin_full_bp.route('/claims/<claim_id>/audit', methods=['POST'])
@admin_required
def audit_claim(claim_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT item_id FROM claim_form WHERE claim_id = %s", (claim_id,))
        claim = cursor.fetchone()
        
        if not claim:
            return jsonify({'code': 404, 'message': '认领记录不存在'}), 404
        
        data = request.get_json()
        status = data.get('status')
        audit_remark = data.get('audit_remark', '')
        
        if status not in ['approved', 'rejected']:
            return jsonify({'code': 400, 'message': '无效的审核状态'}), 400
        
        cursor.execute("""
            UPDATE claim_form 
            SET status = %s, audit_time = %s, audit_remark = %s 
            WHERE claim_id = %s
        """, (status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), audit_remark, claim_id))
        
        if status == 'approved':
            cursor.execute("""
                UPDATE lost_item 
                SET status = 'claimed', found_time = %s 
                WHERE item_id = %s
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), claim[0]))
        
        conn.commit()
        
        log_action('audit_claim', 'claim_record', claim_id, f'审核认领申请, 结果: {status}')
        
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

@admin_full_bp.route('/categories', methods=['GET'])
@admin_required
def get_categories():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT * FROM categories ORDER BY sort_order")
        categories = cursor.fetchall()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': categories
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_full_bp.route('/categories', methods=['POST'])
@admin_required
def create_category():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({'code': 400, 'message': '分类名称不能为空'}), 400
        
        cursor.execute("SELECT * FROM categories WHERE name = %s", (data['name'],))
        existing = cursor.fetchone()
        if existing:
            return jsonify({'code': 400, 'message': '分类名称已存在'}), 400
        
        cursor.execute("""
            INSERT INTO categories (name, description, sort_order, is_active)
            VALUES (%s, %s, %s, %s)
        """, (data['name'], data.get('description', ''), data.get('sort_order', 0), data.get('is_active', True)))
        
        conn.commit()
        
        return jsonify({
            'code': 201,
            'message': '创建成功'
        }), 201
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_full_bp.route('/categories/<category_id>', methods=['PUT'])
@admin_required
def update_category(category_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM categories WHERE id = %s", (category_id,))
        category = cursor.fetchone()
        
        if not category:
            return jsonify({'code': 404, 'message': '分类不存在'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            cursor.execute("SELECT * FROM categories WHERE name = %s AND id != %s", (data['name'], category_id))
            existing = cursor.fetchone()
            if existing:
                return jsonify({'code': 400, 'message': '分类名称已存在'}), 400
            
            cursor.execute("UPDATE categories SET name = %s WHERE id = %s", (data['name'], category_id))
        
        if 'description' in data:
            cursor.execute("UPDATE categories SET description = %s WHERE id = %s", (data['description'], category_id))
        if 'sort_order' in data:
            cursor.execute("UPDATE categories SET sort_order = %s WHERE id = %s", (data['sort_order'], category_id))
        if 'is_active' in data:
            cursor.execute("UPDATE categories SET is_active = %s WHERE id = %s", (data['is_active'], category_id))
        
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

@admin_full_bp.route('/categories/<category_id>', methods=['DELETE'])
@admin_required
def delete_category(category_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM categories WHERE id = %s", (category_id,))
        category = cursor.fetchone()
        
        if not category:
            return jsonify({'code': 404, 'message': '分类不存在'}), 404
        
        cursor.execute("SELECT COUNT(*) FROM lost_item WHERE category_id = %s", (category_id,))
        items_count = cursor.fetchone()[0]
        
        if items_count > 0:
            return jsonify({'code': 400, 'message': f'该分类下有{items_count}个物品，无法删除'}), 400
        
        cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
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

@admin_full_bp.route('/statistics/overview', methods=['GET'])
@admin_required
def get_statistics_overview():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM lost_item")
        total_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM lost_item WHERE audit_status = 'pending'")
        pending_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM lost_item WHERE audit_status = 'approved'")
        approved_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM lost_item WHERE status = 'claimed'")
        claimed_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM claim_form")
        total_claims = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM claim_form WHERE status = 'pending'")
        pending_claims = cursor.fetchone()[0]
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'total_users': total_users,
                'total_items': total_items,
                'pending_items': pending_items,
                'approved_items': approved_items,
                'claimed_items': claimed_items,
                'total_claims': total_claims,
                'pending_claims': pending_claims
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_full_bp.route('/statistics/items-by-category', methods=['GET'])
@admin_required
def get_items_by_category():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT c.name, COUNT(l.item_id) as count
            FROM categories c
            LEFT JOIN lost_item l ON c.id = l.category_id
            GROUP BY c.id
            ORDER BY c.sort_order
        """)
        
        data = cursor.fetchall()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_full_bp.route('/statistics/items-by-status', methods=['GET'])
@admin_required
def get_items_by_status():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT status, COUNT(item_id) as count
            FROM lost_item
            GROUP BY status
        """)
        
        status_map = {
            'pending': '待认领',
            'claimed': '已认领',
            'closed': '已关闭',
            '0': '未找到',
            '1': '已找到'
        }
        
        results = cursor.fetchall()
        data = [{'status': status_map.get(row['status'], row['status']), 'count': row['count']} for row in results]
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_full_bp.route('/statistics/items-trend', methods=['GET'])
@admin_required
def get_items_trend():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        days = int(request.args.get('days', 7))
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT DATE(publish_time) as date, COUNT(item_id) as count
            FROM lost_item
            WHERE publish_time >= %s
            GROUP BY DATE(publish_time)
            ORDER BY DATE(publish_time)
        """, (start_date,))
        
        data = cursor.fetchall()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_full_bp.route('/statistics/user-activity', methods=['GET'])
@admin_required
def get_user_activity():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 10))
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT u.id, u.username, COUNT(l.item_id) as item_count
            FROM users u
            JOIN lost_item l ON u.id = l.publisher_id
            WHERE l.publish_time >= %s
            GROUP BY u.id
            ORDER BY item_count DESC
            LIMIT %s
        """, (start_date, limit))
        
        data = cursor.fetchall()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_full_bp.route('/logs', methods=['GET'])
@admin_required
def get_logs():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        action = request.args.get('action', '')
        user_id = request.args.get('user_id', '')
        
        query = "SELECT * FROM system_logs WHERE 1=1"
        params = []
        
        if action:
            query += " AND action = %s"
            params.append(action)
        
        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)
        
        query += " ORDER BY created_at DESC"
        
        total_query = "SELECT COUNT(*) FROM system_logs WHERE 1=1"
        total_params = []
        if action:
            total_query += " AND action = %s"
            total_params.append(action)
        if user_id:
            total_query += " AND user_id = %s"
            total_params.append(user_id)
        
        cursor.execute(total_query, total_params)
        total = cursor.fetchone()['COUNT(*)']
        
        offset = (page - 1) * per_page
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        logs = cursor.fetchall()
        
        pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'logs': logs,
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

@admin_full_bp.route('/configs', methods=['GET'])
@admin_required
def get_configs():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT * FROM system_configs")
        configs = cursor.fetchall()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': configs
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_full_bp.route('/configs/<config_key>', methods=['PUT'])
@admin_required
def update_config(config_key):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM system_configs WHERE config_key = %s", (config_key,))
        config = cursor.fetchone()
        
        if not config:
            return jsonify({'code': 404, 'message': '配置项不存在'}), 404
        
        data = request.get_json()
        
        if 'config_value' in data:
            cursor.execute("UPDATE system_configs SET config_value = %s WHERE config_key = %s", 
                          (data['config_value'], config_key))
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

def log_action(action, target_type, target_id, detail):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO system_logs (user_id, action, target_type, target_id, detail, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (0, action, target_type, target_id, detail, request.remote_addr))
        
        conn.commit()
    except Exception as e:
        print(f"日志记录失败: {e}")
        if conn: conn.rollback()
    finally:
        if cursor: cursor.close()
        if conn: conn.close()