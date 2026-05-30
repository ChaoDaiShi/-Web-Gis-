from flask import Blueprint, request, jsonify
import pymysql
from datetime import datetime
import json
import base64
import os

claim_bp = Blueprint('claim', __name__)

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}


@claim_bp.route('/api/my/claim', methods=['GET'])
def my_claim():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': '用户ID不能为空'}), 400

    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT c.claim_id, l.title, l.type, c.create_time, c.status, l.item_id
            FROM claim c
            JOIN lost_item l ON c.item_id = l.item_id
            WHERE c.claimer_id = %s
            ORDER BY c.create_time DESC
        """, (int(user_id),))

        items = cursor.fetchall()

        result = []
        for item in items:
            result.append({
                "claim_id": item['claim_id'],
                "title": item['title'],
                "type": item['type'],
                "create_time": str(item['create_time']) if item['create_time'] else '',
                "status": item['status'],
                "item_id": item['item_id']
            })

        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": result})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@claim_bp.route('/api/my/claim', methods=['POST'])
def add_my_claim():
    data = request.get_json()
    user_id = data.get('user_id')
    item_id = data.get('item_id')

    if not user_id:
        return jsonify({'success': False, 'message': '用户ID不能为空'}), 400

    if not item_id:
        return jsonify({'success': False, 'message': '物品ID不能为空'}), 400

    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO claim (item_id, claimer_id, create_time, status)
            VALUES (%s, %s, %s, %s)
        """, (int(item_id), int(user_id), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "认领记录创建成功"})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@claim_bp.route('/api/my/claim/by-item/<int:item_id>', methods=['DELETE'])
def delete_claim_by_item(item_id):
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': '用户ID不能为空'}), 400

    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM claim WHERE item_id = %s AND claimer_id = %s", (item_id, int(user_id)))
        
        if cursor.rowcount > 0:
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"success": True, "message": "删除认领记录成功"})
        else:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "未找到该认领记录"}), 404
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@claim_bp.route('/api/my/claim/<int:claim_id>/cancel', methods=['POST'])
def cancel_my_claim(claim_id):
    data = request.get_json()
    user_id = data.get('user_id')
    item_id = data.get('item_id')

    if not user_id:
        return jsonify({'success': False, 'message': '用户ID不能为空'}), 400

    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM claim WHERE claim_id = %s AND claimer_id = %s", (claim_id, int(user_id)))
        
        if cursor.rowcount > 0:
            if item_id:
                cursor.execute("""
                    UPDATE lost_item 
                    SET status = %s 
                    WHERE item_id = %s
                """, (0, int(item_id)))
            
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"success": True, "message": "取消认领成功"})
        else:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "未找到该认领记录"}), 404
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@claim_bp.route('/api/my/claim-forms', methods=['POST'])
def submit_claim_form():
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

        for key, file in request.files.items():
            if key.startswith('proof_images') and file and file.filename:
                ext = os.path.splitext(file.filename)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    file_data = file.read()
                    base64_encoded = base64.b64encode(file_data).decode('utf-8')
                    mime_type = f"image/{ext[1:]}" if ext[1:] != 'jpeg' else 'image/jpeg'
                    data_url = f"data:{mime_type};base64,{base64_encoded}"
                    proof_images.append(data_url)

        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO claim_form 
            (item_id, applicant_name, applicant_phone, applicant_email, claim_reason, item_description, user_id, proof_images, status, create_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            int(item_id) if item_id else None,
            applicant_name,
            applicant_phone,
            applicant_email,
            claim_reason,
            item_description,
            int(user_id) if user_id else None,
            json.dumps(proof_images) if proof_images else None,
            0,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))

        claim_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': '提交成功', 'claim_id': claim_id})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
