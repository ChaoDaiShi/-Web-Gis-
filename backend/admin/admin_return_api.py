from flask import Blueprint, request, jsonify
from datetime import datetime
import pymysql
import json
import base64
import os
from admin.admin_common import get_conn, send_return_notification

admin_return_api_bp = Blueprint('admin_return_api', __name__)

@admin_return_api_bp.route('/return-forms', methods=['GET'])
def get_return_forms():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT rf.*, u.username as returner_username
            FROM return_form rf
            LEFT JOIN user u ON rf.user_id = u.user_id
            ORDER BY rf.create_time DESC
        """)
        return_forms = cursor.fetchall()
        
        status_labels = ['待审核', '已通过', '已拒绝']
        result = []
        for form in return_forms:
            st = form['status'] if form['status'] is not None else 0
            result.append({
                'return_id': form['return_id'],
                'item_id': form['item_id'],
                'user_id': form.get('user_id'),
                'returner_name': form.get('returner_username') or form.get('applicant_name'),
                'applicant_name': form.get('applicant_name'),
                'contact_info': form.get('applicant_phone'),
                'applicant_phone': form.get('applicant_phone'),
                'return_reason': form.get('return_reason'),
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

@admin_return_api_bp.route('/return-forms/<int:return_id>', methods=['GET'])
def get_return_form_detail(return_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT rf.*, u.username as returner_username, li.title as item_title
            FROM return_form rf
            LEFT JOIN user u ON rf.user_id = u.user_id
            LEFT JOIN lost_item li ON rf.item_id = li.item_id
            WHERE rf.return_id = %s
        """, (return_id,))
        return_form = cursor.fetchone()
        
        if not return_form:
            return jsonify({'code': 404, 'message': '归还记录不存在'}), 404
        
        return jsonify({'code': 200, 'message': 'success', 'data': return_form})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_return_api_bp.route('/return-forms', methods=['POST'])
def add_return_form():
    try:
        applicant_name = request.form.get('applicant_name', '').strip() or request.form.get('returner_name', '').strip()
        applicant_phone = request.form.get('applicant_phone', '').strip() or request.form.get('returner_phone', '').strip()
        return_reason = request.form.get('return_reason', '').strip()
        item_description = request.form.get('item_description', '').strip()
        user_id = request.form.get('user_id')
        item_id = request.form.get('item_id')
        
        if not applicant_phone:
            return jsonify({'success': False, 'message': '联系方式不能为空'})
        
        if not return_reason:
            return jsonify({'success': False, 'message': '归还理由不能为空'})
        
        proof_images = []
        for key in request.files:
            if key.startswith('proof_images') and key != 'proof_images':
                file = request.files[key]
                if file and file.filename:
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
            INSERT INTO return_form 
            (item_id, applicant_name, applicant_phone, return_reason, item_description, user_id, proof_images, status, create_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            int(item_id) if item_id else None,
            applicant_name,
            applicant_phone,
            return_reason,
            item_description,
            int(user_id) if user_id else None,
            json.dumps(proof_images) if proof_images else None,
            0,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        return_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({'success': True, 'message': '提交成功', 'return_id': return_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_return_api_bp.route('/return-forms/<return_id>/approve', methods=['POST'])
def approve_return_form(return_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT item_id, user_id FROM return_form WHERE return_id = %s", (return_id,))
        return_form = cursor.fetchone()
        
        if not return_form:
            return jsonify({'code': 404, 'message': '归还记录不存在'}), 404
        
        cursor.execute("UPDATE return_form SET status = 1 WHERE return_id = %s", (return_id,))
        if return_form[0]:
            cursor.execute("UPDATE lost_item SET status = 1 WHERE item_id = %s", (return_form[0],))
        if return_form[1]:
            send_return_notification(return_form[1], True, return_form[0])
        
        conn.commit()
        
        return jsonify({'code': 200, 'message': '通过成功', 'success': True})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_return_api_bp.route('/return-forms/<return_id>/reject', methods=['POST'])
def reject_return_form(return_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT item_id, user_id FROM return_form WHERE return_id = %s", (return_id,))
        return_form = cursor.fetchone()
        
        if not return_form:
            return jsonify({'code': 404, 'message': '归还记录不存在'}), 404
        
        user_id = return_form[1]
        item_id = return_form[0]
        
        cursor.execute("UPDATE return_form SET status = 2 WHERE return_id = %s", (return_id,))
        
        if user_id:
            send_return_notification(user_id, False, item_id)
        
        conn.commit()
        
        return jsonify({'code': 200, 'message': '拒绝成功', 'success': True})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()