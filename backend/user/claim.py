from flask import Blueprint, request, jsonify
import pymysql
from datetime import datetime
from common.db_config import get_conn

claim_bp = Blueprint('claim', __name__)


@claim_bp.route('/api/my/claim', methods=['GET'])
def my_claim():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': '用户ID不能为空'}), 400

    try:
        conn = get_conn()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT cf.claim_id, li.title, li.type, cf.create_time, cf.status, li.item_id
            FROM claim_form cf
            JOIN lost_item li ON cf.item_id = li.item_id
            WHERE cf.user_id = %s
            ORDER BY cf.create_time DESC
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
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO claim_form (item_id, user_id, create_time, status)
            VALUES (%s, %s, %s, 0)
        """, (int(item_id), int(user_id), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

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
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM claim_form WHERE item_id = %s AND user_id = %s", (item_id, int(user_id)))
        
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
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM claim_form WHERE claim_id = %s AND user_id = %s", (claim_id, int(user_id)))
        
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
