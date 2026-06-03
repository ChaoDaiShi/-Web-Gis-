
from flask import Blueprint, request, jsonify
import pymysql
from datetime import datetime
import json
import base64
import os

verify_bp = Blueprint('verify', __name__)

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

@verify_bp.route('/api/my/verify', methods=['POST'])
def submit_verify():
    try:
        identity = request.form.get('identity', '').strip()
        real_name = request.form.get('real_name', '').strip()
        student_id = request.form.get('student_id', '').strip()
        school = request.form.get('school', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        user_id = request.form.get('user_id')

        if not identity:
            return jsonify({'success': False, 'message': '请选择身份'})

        valid_identities = ['student', 'teacher', 'maintenance', 'staff']
        if identity not in valid_identities:
            return jsonify({'success': False, 'message': '无效的身份选择'})

        if not real_name:
            return jsonify({'success': False, 'message': '真实姓名不能为空'})

        if not student_id:
            identity_labels = {
                'student': '学号',
                'teacher': '教师工号',
                'maintenance': '维修员工号',
                'staff': '教职工号'
            }
            return jsonify({'success': False, 'message': f'{identity_labels.get(identity, "工号")}不能为空'})

        if not phone and not email:
            return jsonify({'success': False, 'message': '手机号和邮箱至少填写一项'})

        if phone and not phone.isdigit():
            return jsonify({'success': False, 'message': '手机号格式不正确'})

        id_card_front = None
        id_card_back = None

        if 'id_card_front' in request.files:
            file = request.files['id_card_front']
            if file and file.filename:
                file_data = file.read()
                base64_encoded = base64.b64encode(file_data).decode('utf-8')
                ext = os.path.splitext(file.filename)[1].lower()
                mime_type = f"image/{ext[1:]}" if ext[1:] != 'jpeg' else 'image/jpeg'
                id_card_front = f"data:{mime_type};base64,{base64_encoded}"

        if 'id_card_back' in request.files:
            file = request.files['id_card_back']
            if file and file.filename:
                file_data = file.read()
                base64_encoded = base64.b64encode(file_data).decode('utf-8')
                ext = os.path.splitext(file.filename)[1].lower()
                mime_type = f"image/{ext[1:]}" if ext[1:] != 'jpeg' else 'image/jpeg'
                id_card_back = f"data:{mime_type};base64,{base64_encoded}"

        if not id_card_front:
            return jsonify({'success': False, 'message': '请上传身份证正面照片'})

        if not id_card_back:
            return jsonify({'success': False, 'message': '请上传身份证反面照片'})

        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO user_verify 
            (user_id, identity, real_name, id_card, student_id, school, phone, email, id_card_front, id_card_back, status, create_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            int(user_id) if user_id else None,
            identity,
            real_name,
            '',  
            student_id,
            school,
            phone,
            email,
            id_card_front,
            id_card_back,
            0,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))

        verify_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': '认证申请提交成功', 'verify_id': verify_id})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)})

@verify_bp.route('/api/my/verify/status', methods=['GET'])
def get_verify_status():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': '用户ID不能为空'}), 400

    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT status, create_time, update_time, message
            FROM user_verify 
            WHERE user_id = %s 
            ORDER BY create_time DESC 
            LIMIT 1
        """, (int(user_id),))

        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            status_map = {
                0: '待审核',
                1: '已通过',
                2: '已拒绝'
            }
            result['status_text'] = status_map.get(result['status'], '未知')
            return jsonify({"success": True, "data": result})
        else:
            return jsonify({"success": True, "data": None})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
