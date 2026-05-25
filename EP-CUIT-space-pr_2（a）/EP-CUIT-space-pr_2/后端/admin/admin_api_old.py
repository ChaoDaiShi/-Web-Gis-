import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import pymysql
import json
import time

admin_api_bp = Blueprint('admin_api', __name__)

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
        auth = request.headers.get('Authorization')
        if not auth or not auth.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未授权'}), 401
        
        token = auth[7:]
        if token != 'admin_token':
            return jsonify({'code': 403, 'message': '需要管理员权限'}), 403
        
        return fn(*args, **kwargs)
    return wrapper

def send_claim_notification(user_id, is_approved, item_id=None):
    item_title = None
    
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        if item_id:
            cursor.execute("SELECT title FROM lost_item WHERE item_id = %s", (item_id,))
            result = cursor.fetchone()
            if result:
                item_title = result[0]
        
        item_name = item_title or '未知物品'
        
        if is_approved:
            title = f"{item_name}认领申请通过"
            content = f"您的「物品ID：{item_id}，物品名：{item_name}」认领申请已通过，请联系拾物者进行物品交接。"
        else:
            title = f"{item_name}认领申请未通过"
            content = f"您的「物品ID：{item_id}，物品名：{item_name}」认领申请未通过，请检查填写信息是否正确或重新提交申请。"
        
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO messages (user_id, title, content, message_type, create_time, is_read, is_deleted)
            VALUES (%s, %s, %s, 'claim', %s, FALSE, FALSE)
        """, (user_id, title, content, local_time))
        
        conn.commit()
    except Exception as e:
        print(f"发送认领通知失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def send_return_notification(user_id, is_approved, item_id=None):
    item_title = None
    
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        if item_id:
            cursor.execute("SELECT title FROM lost_item WHERE item_id = %s", (item_id,))
            result = cursor.fetchone()
            if result:
                item_title = result[0]
        
        item_name = item_title or '未知物品'
        
        if is_approved:
            title = f"{item_name}归还申请通过"
            content = f"您的「物品ID：{item_id}，物品名：{item_name}」归还申请已通过，请联系失主进行物品交接。"
        else:
            title = f"{item_name}归还申请未通过"
            content = f"您的「物品ID：{item_id}，物品名：{item_name}」归还申请未通过，请检查填写信息是否正确或重新提交申请。"
        
        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO messages (user_id, title, content, message_type, create_time, is_read, is_deleted)
            VALUES (%s, %s, %s, 'return', %s, FALSE, FALSE)
        """, (user_id, title, content, local_time))
        
        conn.commit()
    except Exception as e:
        print(f"发送归还通知失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@admin_api_bp.route('/users', methods=['GET'])
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

@admin_api_bp.route('/users/<user_id>', methods=['PUT'])
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

@admin_api_bp.route('/users/<user_id>', methods=['DELETE'])
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

@admin_api_bp.route('/items/audit', methods=['GET'])
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

@admin_api_bp.route('/items/<item_id>/audit', methods=['POST'])
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

@admin_api_bp.route('/claims/audit', methods=['GET'])
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

@admin_api_bp.route('/claims/<claim_id>/audit', methods=['POST'])
@admin_required
def audit_claim(claim_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT item_id, user_id FROM claim_form WHERE claim_id = %s", (claim_id,))
        claim = cursor.fetchone()
        
        if not claim:
            return jsonify({'code': 404, 'message': '认领记录不存在'}), 404
        
        data = request.get_json()
        status = data.get('status')
        audit_remark = data.get('audit_remark', '')
        
        if status not in ['approved', 'rejected']:
            return jsonify({'code': 400, 'message': '无效的审核状态'}), 400
        
        if status == 'approved':
            cursor.execute("""
                UPDATE claim_form 
                SET status = %s, audit_time = %s, audit_remark = %s 
                WHERE claim_id = %s
            """, (1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), audit_remark, claim_id))
            
            cursor.execute("""
                UPDATE lost_item 
                SET status = 'claimed', found_time = %s 
                WHERE item_id = %s
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), claim[0]))
            
            send_claim_notification(claim[1], True, claim[0])
        else:
            user_id = claim[1]
            item_id = claim[0]
            cursor.execute("DELETE FROM claim_form WHERE claim_id = %s", (claim_id,))
            send_claim_notification(user_id, False, item_id)
        
        conn.commit()
        
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

@admin_api_bp.route('/return-forms', methods=['GET'])
def get_return_forms():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status = request.args.get('status', '')
        
        query = "SELECT * FROM return_form WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        query += " ORDER BY create_time DESC"
        
        total_query = "SELECT COUNT(*) FROM return_form WHERE 1=1"
        total_params = []
        if status:
            total_query += " AND status = %s"
            total_params.append(status)
        
        cursor.execute(total_query, total_params)
        total = cursor.fetchone()['COUNT(*)']
        
        offset = (page - 1) * per_page
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        return_forms = cursor.fetchall()
        
        pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'return_forms': return_forms,
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

@admin_api_bp.route('/return-forms', methods=['POST'])
def submit_return_form():
    try:
        applicant_name = request.form.get('applicant_name', '').strip()
        applicant_phone = request.form.get('applicant_phone', '').strip()
        return_reason = request.form.get('return_reason', '').strip()
        item_description = request.form.get('item_description', '').strip()
        user_id = request.form.get('user_id')
        item_id = request.form.get('item_id')
        
        if not applicant_phone:
            return jsonify({'success': False, 'message': '联系方式不能为空'})
        
        if not return_reason:
            return jsonify({'success': False, 'message': '归还理由不能为空'})
        
        if not item_description:
            return jsonify({'success': False, 'message': '物品描述不能为空'})
        
        proof_images = []
        if 'proof_images' in request.files:
            files = request.files.getlist('proof_images')
            for file in files:
                if file and file.filename:
                    ext = os.path.splitext(file.filename)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                        filename = f"return_proof_{int(time.time())}_{file.filename}"
                        upload_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
                        file.save(os.path.join(upload_path, filename))
                        proof_images.append(f"/uploads/{filename}")
        
        conn = get_conn()
        curs = conn.cursor()
        
        curs.execute("INSERT INTO return_form (item_id, applicant_name, applicant_phone, return_reason, item_description, user_id, proof_images, status, create_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (int(item_id) if item_id else None, applicant_name, applicant_phone, return_reason, item_description, int(user_id) if user_id else None, json.dumps(proof_images) if proof_images else None, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        return_id = curs.lastrowid
        conn.commit()
        
        curs.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '提交成功', 'return_id': return_id})
    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        try:
            curs.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass
        return jsonify({'success': False, 'message': str(e)})

@admin_api_bp.route('/return-forms/<return_id>/approve', methods=['POST'])
@admin_required
def approve_return_form(return_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT item_id, user_id FROM return_form WHERE return_id = %s", (return_id,))
        return_form = cursor.fetchone()
        
        if not return_form:
            return jsonify({'success': False, 'message': '归还记录不存在'})
        
        cursor.execute("UPDATE return_form SET status = 1 WHERE return_id = %s", (return_id,))
        cursor.execute("UPDATE lost_item SET status = 1 WHERE item_id = %s", (return_form[0],))
        
        send_return_notification(return_form[1], True, return_form[0])
        
        conn.commit()
        
        return jsonify({'success': True, 'message': '通过成功'})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_api_bp.route('/return-forms/<return_id>/reject', methods=['POST'])
@admin_required
def reject_return_form(return_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT item_id, user_id FROM return_form WHERE return_id = %s", (return_id,))
        return_form = cursor.fetchone()
        
        if not return_form:
            return jsonify({'success': False, 'message': '归还记录不存在'})
        
        user_id = return_form[1]
        item_id = return_form[0]
        
        cursor.execute("DELETE FROM return_form WHERE return_id = %s", (return_id,))
        
        send_return_notification(user_id, False, item_id)
        
        conn.commit()
        
        return jsonify({'success': True, 'message': '拒绝成功'})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_api_bp.route('/categories', methods=['GET'])
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

@admin_api_bp.route('/categories', methods=['POST'])
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

@admin_api_bp.route('/categories/<category_id>', methods=['PUT'])
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

@admin_api_bp.route('/categories/<category_id>', methods=['DELETE'])
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

@admin_api_bp.route('/statistics/overview', methods=['GET'])
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

@admin_api_bp.route('/statistics/items-by-category', methods=['GET'])
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

@admin_api_bp.route('/statistics/items-by-status', methods=['GET'])
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

@admin_api_bp.route('/lost_items', methods=['GET'])
def get_lost_items():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT * FROM lost_item")
        items = cursor.fetchall()
        
        result = []
        for item in items:
            image_urls = []
            if item['image_urls']:
                try:
                    image_urls = json.loads(item['image_urls'])
                except:
                    image_urls = []
            
            result.append({
                'item_id': item['item_id'],
                'title': item['title'],
                'description': item['description'],
                'type': '拾到' if item['type'] == 1 else '丢失',
                'category_id': item['category_id'],
                'status': ['待认领', '已认领', '已关闭'][item['status']] if item['status'] is not None else '未知',
                'image_urls': image_urls,
                'publisher_id': item['publisher_id'],
                'location_id': item['location_id'],
                'create_time': item['create_time'].strftime('%Y-%m-%d %H:%M:%S') if item['create_time'] else '',
                'update_time': item['update_time'].strftime('%Y-%m-%d %H:%M:%S') if item['update_time'] else ''
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_api_bp.route('/lost_items', methods=['POST'])
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

@admin_api_bp.route('/lost_items/<int:item_id>', methods=['PUT'])
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

@admin_api_bp.route('/lost_items/<int:item_id>', methods=['DELETE'])
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

@admin_api_bp.route('/claim-forms', methods=['GET'])
def get_claim_forms():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT * FROM claim_form ORDER BY create_time DESC")
        claim_forms = cursor.fetchall()
        
        result = []
        for form in claim_forms:
            result.append({
                'claim_id': form['claim_id'],
                'item_id': form['item_id'],
                'applicant_name': form.get('applicant_name', ''),
                'applicant_phone': form.get('applicant_phone', ''),
                'applicant_email': form.get('applicant_email', ''),
                'claim_reason': form.get('claim_reason', ''),
                'item_description': form.get('item_description', ''),
                'status': ['待审核', '已通过', '已拒绝'][form['status']] if form['status'] is not None else '未知',
                'create_time': form['create_time'].strftime('%Y-%m-%d %H:%M:%S') if form['create_time'] else ''
            })
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_api_bp.route('/claim-forms', methods=['POST'])
def add_claim_form():
    conn = None
    cursor = None
    try:
        applicant_name = request.form.get('applicant_name', '').strip()
        applicant_phone = request.form.get('applicant_phone', '').strip()
        applicant_email = request.form.get('applicant_email', '').strip()
        claim_reason = request.form.get('claim_reason', '').strip()
        item_description = request.form.get('item_description', '').strip()
        user_id = request.form.get('user_id')
        item_id = request.form.get('item_id')
        
        if not applicant_phone:
            return jsonify({'success': False, 'message': '联系方式不能为空'})
        
        if not claim_reason or not item_description:
            return jsonify({'success': False, 'message': '认领理由和物品描述不能为空'})
        
        proof_images = []
        if 'proof_images' in request.files:
            files = request.files.getlist('proof_images')
            for file in files:
                if file and file.filename:
                    ext = os.path.splitext(file.filename)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                        filename = f"proof_{int(time.time())}_{file.filename}"
                        upload_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
                        file.save(os.path.join(upload_path, filename))
                        proof_images.append(f"/uploads/{filename}")
        
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO claim_form 
            (item_id, applicant_name, applicant_phone, claim_reason, item_description, user_id, proof_images, status, create_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            int(item_id) if item_id else None,
            applicant_name,
            applicant_phone,
            claim_reason,
            item_description,
            int(user_id) if user_id else None,
            json.dumps(proof_images) if proof_images else None,
            0,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        claim_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({'success': True, 'message': '提交成功', 'claim_id': claim_id})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_api_bp.route('/locations', methods=['GET'])
def get_locations():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT * FROM location")
        locations = cursor.fetchall()
        
        return jsonify(locations)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()