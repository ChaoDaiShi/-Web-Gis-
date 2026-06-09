from flask import Blueprint, request, jsonify
from datetime import datetime
import pymysql
from admin.admin_common import get_conn, admin_required

admin_audit_bp = Blueprint('admin_audit', __name__)

@admin_audit_bp.route('/list', methods=['GET'])
@admin_required
def get_audit_list():
    """获取审核列表，支持筛选"""
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        target_type = request.args.get('target_type')
        status = request.args.get('status', 'pending')
        
        where_clauses = []
        params = []
        
        if target_type:
            where_clauses.append("target_type = %s")
            params.append(target_type)
        if status:
            where_clauses.append("status = %s")
            params.append(status)
        
        where_str = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # 获取总数
        count_sql = f"SELECT COUNT(*) as total FROM audit WHERE {where_str}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']
        
        # 获取分页数据
        offset = (page - 1) * per_page
        sql = f"""
            SELECT a.*, 
                   u.username as requester_name,
                   ad.username as auditor_name
            FROM audit a
            LEFT JOIN user u ON a.requester_id = u.user_id
            LEFT JOIN admin ad ON a.audit_by = ad.admin_id
            WHERE {where_str}
            ORDER BY a.create_time DESC
            LIMIT %s OFFSET %s
        """
        params.extend([per_page, offset])
        cursor.execute(sql, params)
        audit_list = cursor.fetchall()
        
        pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': audit_list,
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

@admin_audit_bp.route('/detail/<int:audit_id>', methods=['GET'])
@admin_required
def get_audit_detail(audit_id):
    """获取审核详情"""
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT a.*, 
                   u.username as requester_name,
                   ad.username as auditor_name
            FROM audit a
            LEFT JOIN user u ON a.requester_id = u.user_id
            LEFT JOIN admin ad ON a.audit_by = ad.admin_id
            WHERE a.audit_id = %s
        """, (audit_id,))
        audit = cursor.fetchone()
        
        if not audit:
            return jsonify({'code': 404, 'message': '审核记录不存在'}), 404
        
        # 根据目标类型获取关联的详细信息
        target_type = audit['target_type']
        target_id = audit['target_id']
        target_detail = None
        
        if target_type == 'lost_item':
            cursor.execute("""
                SELECT li.*, u.username as publisher_name, c.name as category_name
                FROM lost_item li
                LEFT JOIN user u ON li.publisher_id = u.user_id
                LEFT JOIN category c ON li.category_id = c.id
                WHERE li.item_id = %s
            """, (target_id,))
            target_detail = cursor.fetchone()
        elif target_type == 'claim_form':
            cursor.execute("""
                SELECT cf.*, u.username as applicant_name, li.title as item_title
                FROM claim_form cf
                LEFT JOIN user u ON cf.user_id = u.user_id
                LEFT JOIN lost_item li ON cf.item_id = li.item_id
                WHERE cf.claim_id = %s
            """, (target_id,))
            target_detail = cursor.fetchone()
        elif target_type == 'return_form':
            cursor.execute("""
                SELECT rf.*, u.username as returner_name, li.title as item_title
                FROM return_form rf
                LEFT JOIN user u ON rf.user_id = u.user_id
                LEFT JOIN lost_item li ON rf.item_id = li.item_id
                WHERE rf.return_id = %s
            """, (target_id,))
            target_detail = cursor.fetchone()
        elif target_type == 'user_verify':
            cursor.execute("""
                SELECT uv.*, u.username
                FROM user_verify uv
                LEFT JOIN user u ON uv.user_id = u.user_id
                WHERE uv.verify_id = %s
            """, (target_id,))
            target_detail = cursor.fetchone()
        elif target_type == 'appointment':
            cursor.execute("""
                SELECT ap.*, u.username as user_name, li.title as item_title
                FROM appointment ap
                LEFT JOIN user u ON ap.user_id = u.user_id
                LEFT JOIN lost_item li ON ap.item_id = li.item_id
                WHERE ap.appointment_id = %s
            """, (target_id,))
            target_detail = cursor.fetchone()
        elif target_type == 'privilege_request':
            cursor.execute("""
                SELECT pr.*, a.username as admin_name
                FROM privilege_request pr
                LEFT JOIN admin a ON pr.admin_id = a.admin_id
                WHERE pr.request_id = %s
            """, (target_id,))
            target_detail = cursor.fetchone()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'audit': audit,
                'target_detail': target_detail
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_audit_bp.route('/approve/<int:audit_id>', methods=['POST'])
@admin_required
def approve_audit(audit_id):
    """审核通过"""
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # 获取当前管理员ID（从session或token获取）
        data = request.get_json()
        audit_by = data.get('admin_id', 1)  # 临时默认值
        audit_remark = data.get('remark', '')
        
        # 获取审核信息
        cursor.execute("SELECT * FROM audit WHERE audit_id = %s", (audit_id,))
        audit = cursor.fetchone()
        
        if not audit:
            return jsonify({'code': 404, 'message': '审核记录不存在'}), 404
        
        target_type = audit[1]  # target_type
        target_id = audit[2]   # target_id
        
        # 更新审核表
        cursor.execute("""
            UPDATE audit 
            SET status = 'approved', 
                audit_by = %s, 
                audit_time = %s, 
                audit_remark = %s,
                update_time = %s
            WHERE audit_id = %s
        """, (audit_by, datetime.now(), audit_remark, datetime.now(), audit_id))
        
        # 根据目标类型更新对应表
        if target_type == 'lost_item':
            cursor.execute("UPDATE lost_item SET status = 0 WHERE item_id = %s", (target_id,))
        elif target_type == 'claim_form':
            cursor.execute("UPDATE claim_form SET status = 1 WHERE claim_id = %s", (target_id,))
        elif target_type == 'return_form':
            cursor.execute("UPDATE return_form SET status = 1 WHERE return_id = %s", (target_id,))
        elif target_type == 'user_verify':
            cursor.execute("UPDATE user_verify SET status = 1, update_time = %s WHERE verify_id = %s",
                          (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), target_id))
            # 更新用户表的角色
            cursor.execute("""
                UPDATE user u 
                JOIN user_verify uv ON u.user_id = uv.user_id 
                SET u.role = uv.identity 
                WHERE uv.verify_id = %s
            """, (target_id,))
        elif target_type == 'appointment':
            cursor.execute("""
                UPDATE appointment 
                SET status = 'approved', reviewer_id = %s, review_time = %s, review_note = %s, update_time = %s
                WHERE appointment_id = %s
            """, (audit_by, datetime.now(), audit_remark, datetime.now(), target_id))
        elif target_type == 'privilege_request':
            cursor.execute("""
                UPDATE privilege_request 
                SET status = 'approved', reviewer_id = %s, review_time = NOW(), review_note = %s
                WHERE request_id = %s
            """, (audit_by, audit_remark, target_id))
        
        conn.commit()
        
        return jsonify({
            'code': 200,
            'message': '审核通过'
        })
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_audit_bp.route('/reject/<int:audit_id>', methods=['POST'])
@admin_required
def reject_audit(audit_id):
    """审核拒绝"""
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        data = request.get_json()
        audit_by = data.get('admin_id', 1)
        audit_remark = data.get('remark', '')
        
        # 获取审核信息
        cursor.execute("SELECT * FROM audit WHERE audit_id = %s", (audit_id,))
        audit = cursor.fetchone()
        
        if not audit:
            return jsonify({'code': 404, 'message': '审核记录不存在'}), 404
        
        target_type = audit[1]  # target_type
        target_id = audit[2]   # target_id
        
        # 更新审核表
        cursor.execute("""
            UPDATE audit 
            SET status = 'rejected', 
                audit_by = %s, 
                audit_time = %s, 
                audit_remark = %s,
                update_time = %s
            WHERE audit_id = %s
        """, (audit_by, datetime.now(), audit_remark, datetime.now(), audit_id))
        
        # 根据目标类型更新对应表
        if target_type == 'claim_form':
            cursor.execute("UPDATE claim_form SET status = 2 WHERE claim_id = %s", (target_id,))
        elif target_type == 'return_form':
            cursor.execute("UPDATE return_form SET status = 2 WHERE return_id = %s", (target_id,))
        elif target_type == 'user_verify':
            cursor.execute("UPDATE user_verify SET status = 2, update_time = %s WHERE verify_id = %s",
                          (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), target_id))
        elif target_type == 'appointment':
            cursor.execute("""
                UPDATE appointment 
                SET status = 'rejected', reviewer_id = %s, review_time = %s, review_note = %s, update_time = %s
                WHERE appointment_id = %s
            """, (audit_by, datetime.now(), audit_remark, datetime.now(), target_id))
        elif target_type == 'privilege_request':
            cursor.execute("""
                UPDATE privilege_request 
                SET status = 'rejected', reviewer_id = %s, review_time = NOW(), review_note = %s
                WHERE request_id = %s
            """, (audit_by, audit_remark, target_id))
        
        conn.commit()
        
        return jsonify({
            'code': 200,
            'message': '已拒绝审核'
        })
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_audit_bp.route('/create', methods=['POST'])
@admin_required
def create_audit():
    """创建审核记录（内部使用）"""
    conn = None
    cursor = None
    try:
        data = request.get_json()
        
        target_type = data.get('target_type')
        target_id = data.get('target_id')
        requester_id = data.get('requester_id')
        
        if not target_type or not target_id:
            return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
        
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO audit (target_type, target_id, requester_id, status, create_time, update_time)
            VALUES (%s, %s, %s, 'pending', %s, %s)
        """, (target_type, target_id, requester_id, datetime.now(), datetime.now()))
        
        audit_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({
            'code': 200,
            'message': '创建成功',
            'data': {'audit_id': audit_id}
        })
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_audit_bp.route('/stats', methods=['GET'])
@admin_required
def get_audit_stats():
    """获取审核统计信息"""
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 按状态统计
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM audit
            GROUP BY status
        """)
        status_stats = cursor.fetchall()
        
        # 按类型统计
        cursor.execute("""
            SELECT target_type, COUNT(*) as count
            FROM audit
            GROUP BY target_type
        """)
        type_stats = cursor.fetchall()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'status_stats': status_stats,
                'type_stats': type_stats
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
