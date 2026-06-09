from flask import Blueprint, request, jsonify
from datetime import datetime
import pymysql
import json
import base64
import os
from admin.admin_common import get_conn, admin_required, send_claim_notification

admin_claim_api_bp = Blueprint('admin_claim_api', __name__)

@admin_claim_api_bp.route('/claims/audit', methods=['GET'])
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

@admin_claim_api_bp.route('/claims/<claim_id>/audit', methods=['POST'])
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
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                UPDATE claim_form SET status = 1 WHERE claim_id = %s
            """, (claim_id,))
            
            # 同步更新统一审核表 audit
            cursor.execute("""
                UPDATE audit 
                SET status = 'approved', audit_time = %s, audit_remark = %s, update_time = %s
                WHERE target_type = 'claim_form' AND target_id = %s
            """, (now, audit_remark, now, claim_id))
            
            cursor.execute("""
                UPDATE lost_item 
                SET status = 'claimed', found_time = %s 
                WHERE item_id = %s
            """, (now, claim[0]))
            
            send_claim_notification(claim[1], True, claim[0])
        else:
            user_id = claim[1]
            item_id = claim[0]
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("DELETE FROM claim_form WHERE claim_id = %s", (claim_id,))
            # 同步更新统一审核表 audit
            cursor.execute("""
                UPDATE audit 
                SET status = 'rejected', audit_time = %s, audit_remark = %s, update_time = %s
                WHERE target_type = 'claim_form' AND target_id = %s
            """, (now, audit_remark, now, claim_id))
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

@admin_claim_api_bp.route('/claim-forms', methods=['GET'])
def get_claim_forms():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT cf.*, u.username as claimer_username
            FROM claim_form cf
            LEFT JOIN user u ON cf.user_id = u.user_id
            ORDER BY cf.create_time DESC
        """)
        claim_forms = cursor.fetchall()
        
        status_labels = ['待审核', '已通过', '已拒绝']
        result = []
        for form in claim_forms:
            st = form['status'] if form['status'] is not None else 0
            result.append({
                'claim_id': form['claim_id'],
                'item_id': form['item_id'],
                'user_id': form.get('user_id'),
                'claimer_name': form.get('claimer_username') or form.get('applicant_name'),
                'applicant_name': form.get('applicant_name'),
                'contact_info': form.get('applicant_phone'),
                'applicant_phone': form.get('applicant_phone'),
                'applicant_email': form.get('applicant_email'),
                'claim_reason': form.get('claim_reason'),
                'item_description': form.get('item_description'),
                'proof_images': form.get('proof_images') or '',
                'status': st,
                'status_label': status_labels[st] if 0 <= st < len(status_labels) else '未知',
                'create_time': form['create_time'].strftime('%Y-%m-%d %H:%M:%S') if form.get('create_time') else ''
            })
        
        return jsonify({'code': 200, 'message': 'success', 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_claim_api_bp.route('/claim-forms/<int:claim_id>', methods=['GET'])
def get_claim_form_detail(claim_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT cf.*, u.username as claimer_username, li.title as item_title
            FROM claim_form cf
            LEFT JOIN user u ON cf.user_id = u.user_id
            LEFT JOIN lost_item li ON cf.item_id = li.item_id
            WHERE cf.claim_id = %s
        """, (claim_id,))
        claim_form = cursor.fetchone()
        
        if not claim_form:
            return jsonify({'code': 404, 'message': '认领记录不存在'}), 404
        
        return jsonify({'code': 200, 'message': 'success', 'data': claim_form})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_claim_api_bp.route('/claim-forms', methods=['POST'])
def add_claim_form():
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
        
        if len(request.files) > 0:
            for key, file in request.files.items():
                if key.startswith('proof_images') and file and file.filename:
                    ext = os.path.splitext(file.filename)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                        file_data = file.read()
                        base64_encoded = base64.b64encode(file_data).decode('utf-8')
                        mime_type = f"image/{ext[1:]}" if ext[1:] != 'jpeg' else 'image/jpeg'
                        data_url = f"data:{mime_type};base64,{base64_encoded}"
                        proof_images.append(data_url)
        
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
        
        # 同步创建统一审核记录到audit表
        cursor.execute("""
            INSERT INTO audit (target_type, target_id, requester_id, status, create_time, update_time)
            VALUES ('claim_form', %s, %s, 'pending', NOW(), NOW())
        """, (claim_id, int(user_id) if user_id else None))
        conn.commit()
        
        return jsonify({'success': True, 'message': '提交成功', 'claim_id': claim_id})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_claim_api_bp.route('/claim-forms/<int:claim_id>', methods=['DELETE'])
def delete_claim_form(claim_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM claim_form WHERE claim_id = %s", (claim_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return jsonify({'success': True, 'message': '删除成功'})
        else:
            return jsonify({'success': False, 'message': '未找到该认领记录'})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_claim_api_bp.route('/claim-forms/<int:claim_id>/approve', methods=['POST'])
def approve_claim_form(claim_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT item_id, user_id FROM claim_form WHERE claim_id = %s", (claim_id,))
        claim_form = cursor.fetchone()
        
        if not claim_form:
            return jsonify({'code': 404, 'message': '认领记录不存在'}), 404
        
        item_id = claim_form[0]
        user_id = claim_form[1]
        
        cursor.execute("UPDATE claim_form SET status = 1 WHERE claim_id = %s", (claim_id,))
        
        # 同步更新统一审核表 audit
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            UPDATE audit 
            SET status = 'approved', audit_time = %s, update_time = %s
            WHERE target_type = 'claim_form' AND target_id = %s
        """, (now, now, claim_id))
        
        if item_id is not None:
            cursor.execute("UPDATE lost_item SET status = 1 WHERE item_id = %s", (item_id,))
        
        if user_id is not None:
            send_claim_notification(user_id, True, item_id)
        
        conn.commit()
        
        return jsonify({'code': 200, 'message': '通过成功', 'success': True})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_claim_api_bp.route('/claim-forms/<int:claim_id>/reject', methods=['POST'])
def reject_claim_form(claim_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT item_id, user_id FROM claim_form WHERE claim_id = %s", (claim_id,))
        claim_form = cursor.fetchone()
        
        if not claim_form:
            return jsonify({'code': 404, 'message': '认领记录不存在'}), 404
        
        item_id = claim_form[0]
        user_id = claim_form[1]
        
        cursor.execute("UPDATE claim_form SET status = 2 WHERE claim_id = %s", (claim_id,))
        
        # 同步更新统一审核表 audit
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            UPDATE audit 
            SET status = 'rejected', audit_time = %s, update_time = %s
            WHERE target_type = 'claim_form' AND target_id = %s
        """, (now, now, claim_id))
        
        if user_id is not None:
            send_claim_notification(user_id, False, item_id)
        
        conn.commit()
        
        return jsonify({'code': 200, 'message': '拒绝成功', 'success': True})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()